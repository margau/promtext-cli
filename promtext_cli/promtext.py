"""module providing the core functionality"""

import argparse
import logging
import sys
from pathlib import Path

from prometheus_client import CollectorRegistry, Gauge, write_to_textfile
from prometheus_client.parser import text_string_to_metric_families


class Promtext:
    """Class for the core functionality"""

    def __init__(self):
        self.textfile = None
        self.logger = None
        self.args = None
        self.registry = CollectorRegistry()

        self.metrics = {}

    def _arguments(self):
        """Load every input item from arguments & define cli"""
        # required file first
        parser = argparse.ArgumentParser(description="Prometheus textfile helper")
        parser.add_argument(
            "filename",
            type=str,
            help="Path to existing or new prometheus textfile, will be updated",
        )

        # metric name, required
        parser.add_argument("metric", type=str, help="metric name (new or updated)")

        # metric value as int/float, required
        parser.add_argument("value", type=float, help="metric value")

        # metric documentation as optional argument
        parser.add_argument(
            "--docs",
            type=str,
            help="metric documentation",
            default="metric appended by promtext-cli",
        )

        # labels, key-value, minimum 0, repeatable
        parser.add_argument(
            "--label",
            metavar="KEY=VALUE",
            help="label key=value pairs",
            action="append",
        )

        # log level from argparse
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_const",
            dest="loglevel",
            const=logging.INFO,
        )
        self.args = parser.parse_args()

        # processing: check if file is available, if yes, parse
        self.textfile = Path(self.args.filename)

    def parse_file(self):
        """If possible, convert the input textfile to metrics in the registry"""
        # check if self.args.filename exists with pathlib
        if self.textfile.is_file():
            for f in text_string_to_metric_families(
                self.textfile.read_text(encoding="utf-8"),
            ):
                # per metric: iterate over samples, create metric in registry
                m = False
                samples = list(f.samples)
                if len(samples) > 0:
                    # if we have samples, use the labelnames from them
                    labelnames = list(samples[0].labels.keys())
                    # metric-type specific init
                    if f.type == "gauge":
                        m = Gauge(
                            f.name,
                            f.documentation,
                            unit=f.unit,
                            labelnames=labelnames,
                            registry=self.registry,
                        )
                    else:
                        # we don't support other types yet, continue in these cases
                        self.logger.warning(
                            "unsupported metric type %s, dropping",
                            f.type,
                        )
                        continue
                    for s in samples:
                        if len(labelnames) > 0:
                            labelvalues = list(s.labels.values())
                            m.labels(*labelvalues).set(s.value)
                        else:
                            m.set(s.value)
                    self.metrics[f.name] = m
                    self.logger.info(
                        "copy gauge metric %s with labels %s from old file",
                        f.name,
                        ", ".join(labelnames),
                    )
                else:
                    self.logger.warning(
                        "got empty metric %s from old file, dropping",
                        f.name,
                    )

    def _build_metrics(self):
        # add new metric from commandline
        m = False

        # figure out labelkey- and values
        labels = {}
        if self.args.label:
            for lpair in self.args.label:
                k, v = lpair.split("=")
                labels[k] = v

        labelvalues = []
        # here, we use a new metric
        if self.args.metric not in self.metrics:
            self.logger.info("adding new metric %s", self.args.metric)
            m = Gauge(
                self.args.metric,
                self.args.docs,
                registry=self.registry,
                labelnames=labels.keys(),
            )
            labelvalues = labels.values()
        else:
            m = self.metrics[self.args.metric]

            # There is no way to access existing labelnames directly
            # pylint: disable=W0212
            old_labelnames = list(m._labelnames)  # noqa: SLF001
            for la in old_labelnames:
                self.logger.info("processing label %s", la)
                if la in labels:  # labelvalues are needed in order!
                    labelvalues.append(labels[la])
                else:
                    self.logger.error(
                        "previously known label '%s' missing, cannot update!",
                        la,
                    )
                    sys.exit(1)
            if len(old_labelnames) != len(labels.keys()):
                self.logger.error(
                    """labelnames for metric %s not the same, cannot update!
                    Old: %s, New: %s""",
                    self.args.metric,
                    old_labelnames,
                    list(labels.keys()),
                )
                sys.exit(1)
            self.logger.info("updating metric %s", self.args.metric)

        # actually set the value
        if len(labelvalues) > 0:
            m.labels(*labelvalues).set(self.args.value)
        else:
            m.set(self.args.value)

    def output_file(self):
        """Output to a textfile"""
        write_to_textfile(self.textfile, self.registry)
        self.logger.info("wrote to %s", self.textfile)

    def cli_entrypoint(self):
        """Main method called from the CLI"""
        self._arguments()

        logging.basicConfig(level=self.args.loglevel)
        self.logger = logging.getLogger(__name__)

        self.parse_file()
        self._build_metrics()
        self.output_file()
