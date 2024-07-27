"""promtext_cli is providing a CLI to cleanly update prometheus textfiles from scripts"""

import argparse
from pathlib import Path
import logging
import sys

from prometheus_client.parser import text_string_to_metric_families
from prometheus_client import CollectorRegistry, Gauge, write_to_textfile

def promtext():
    # setup argpars
    # required file first
    parser = argparse.ArgumentParser(description='Prometheus textfile helper')
    parser.add_argument(
        'filename', 
        type=str,
        help='Path to existing or new prometheus textfile, will be updated'
        )

    # metric name, required
    parser.add_argument(
        'metric', 
        type=str,
        help='metric name (new or updated)')

    # metric value as int/float, required
    parser.add_argument('value', type=float, help='metric value')

    # metric documentation as optional argument
    parser.add_argument(
        '--docs', type=str, 
        help='metric documentation', default="metric appended by promtext-cli")

    # labels, key-value, minimum 0, repeatable
    parser.add_argument("--label", metavar="KEY=VALUE", help='label key=value pairs', action='append')

    # log level from argparse
    parser.add_argument(
        '-v', '--verbose',
        action="store_const", dest="loglevel", const=logging.INFO,
    )
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    logger = logging.getLogger(__name__)

    # processing: check if file is available, if yes, parse
    textfile = Path(args.filename)

    registry = CollectorRegistry()
    metrics = {}

    # check if args.filename exists with pathlib
    if textfile.is_file():
        for f in text_string_to_metric_families(textfile.read_text()):
            # per metric: iterate over samples, create metric in registry
            m = False
            samples = []
            for s in f.samples:
                samples.append(s)
            if len(samples) > 0:
                # if we have samples, use the labelnames from them
                labelnames = list(samples[0].labels.keys())
                # metric-type specific init
                if f.type == "gauge":
                    m = Gauge(f.name, f.documentation,
                        unit=f.unit, labelnames=labelnames, registry=registry)
                else:
                    # we don't support other types yet, continue in these cases
                    logger.warning("unsupported metric type %s, dropping", f.type)
                    continue
                for s in samples:
                    if len(labelnames) > 0:
                        labelvalues = list(s.labels.values())
                        m.labels(*labelvalues).set(s.value)
                    else:
                        m.set(s.value)
                metrics[f.name] = m
                logger.info("copy gauge metric %s with labels %s from old file",
                    f.name, ', '.join(labelnames))
            else:
                logger.warning("got empty metric %s from old file, dropping", f.name)

    # add new metric from commandline
    m = False

    # figure out labelkey- and values
    labels = {}
    if args.label:
        for lpair in args.label:
            k, v = lpair.split("=")
            labels[k] = v

    labelvalues = []
    # here, we use a new metric
    if args.metric not in metrics:
        logger.info("adding new metric %s", args.metric)
        m = Gauge(args.metric, args.docs, registry=registry, labelnames=labels.keys())
        labelvalues = labels.values()
    else:
        m = metrics[args.metric]
        
        old_labelnames = list(m._labelnames)
        for la in old_labelnames:
            logger.info("processing label %s", la)
            if la in labels: # labelvalues are needed in order!
                labelvalues.append(labels[la])
            else:
                logger.error("previously known label '%s' missing, cannot update!", la)
                sys.exit(1)
        if len(old_labelnames) != len(labels.keys()):
            logger.error("labelnames for metric %s not the same, cannot update! Old: %s, New: %s",
                args.metric, old_labelnames, list(labels.keys()))
            sys.exit(1)
        logger.info("updating metric %s", args.metric)

    # actually set the value
    if len(labelvalues) > 0:
        m.labels(*labelvalues).set(args.value)
    else:
        m.set(args.value)

    # write to file
    write_to_textfile(args.filename, registry)
    logger.info("wrote to %s", args.filename)

if __name__ == '__main__':
    promtext()
