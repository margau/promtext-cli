# pylint: disable=R0801
"""This script does blackbox-like testing of the promtext cli tool"""

import shutil
from cli_test_helpers import shell


def test_entrypoint():
    """
    Is entrypoint script installed? (pyproject.toml)
    """
    assert shutil.which("promtext")


def test_help():
    """
    Does the help command work?
    """
    result = shell("promtext --help")
    assert result.exit_code == 0
    assert "usage:" in result.stdout


def test_empty():
    """
    Does the command fails with no arguments?
    """
    result = shell("promtext")
    assert result.exit_code == 2
    assert "usage:" in result.stderr


def test_new_file(tmp_path):
    """
    Does the command create a new file with metrics content?
    """
    promfile = tmp_path / "new_file.prom"
    result = shell(f"promtext {promfile} test_metric 0")
    assert result.exit_code == 0
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP test_metric metric appended by promtext-cli"
        "\n"
        "# TYPE test_metric gauge"
        "\n"
        "test_metric 0.0"
        "\n"
    )
