# pylint: disable=R0801,W0511
"""Functional testing by calling the methods directly"""

import pytest
from cli_test_helpers import ArgvContext

from promtext_cli.main import main as promtext_main


def test_new_file(tmp_path):
    """Does the command create a new file with metrics content?"""
    promfile = tmp_path / "new_file.prom"
    with ArgvContext("promtext", str(promfile), "test_metric", "0"):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP test_metric metric appended by promtext-cli"
        "\n"
        "# TYPE test_metric gauge"
        "\n"
        "test_metric 0.0"
        "\n"
    )


def test_labels(tmp_path):
    """Does the command create a new file with metrics content?"""
    promfile = tmp_path / "label_file.prom"
    with ArgvContext(
        "promtext",
        "--label",
        "testlabel=testvalue",
        str(promfile),
        "test_metric",
        0,
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP test_metric metric appended by promtext-cli"
        "\n"
        "# TYPE test_metric gauge"
        "\n"
        'test_metric{testlabel="testvalue"} 0.0'
        "\n"
    )


def test_existing_metric_append_metric(tmp_path):
    """Does the command append a new metric to an existing file
    with metrics content and preserve existing metrics?
    """
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="testvalue"} 0.0'
        "\n",
    )
    with ArgvContext(
        "promtext",
        "--label",
        "testlabel=testvalue",
        str(promfile),
        "new_metric",
        0,
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="testvalue"} 0.0'
        "\n"
        "# HELP new_metric metric appended by promtext-cli"
        "\n"
        "# TYPE new_metric gauge"
        "\n"
        'new_metric{testlabel="testvalue"} 0.0'
        "\n"
    )


def test_existing_metric_append_labelvalue(tmp_path):
    """Does the command append a new metric to an existing file
    with metrics content and preserve existing metrics?
    """
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="existing"} 0.0'
        "\n",
    )
    with ArgvContext(
        "promtext",
        "--label",
        "testlabel=new",
        str(promfile),
        "existing_metric",
        0,
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="existing"} 0.0'
        "\n"
        'existing_metric{testlabel="new"} 0.0'
        "\n"
    )


def test_existing_metric_multilabel(tmp_path):
    """Does the command append a new metric to an existing file
    with metrics content and preserve existing metrics?
    """
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{first="existing", second="existing"} 0.0'
        "\n",
    )
    with ArgvContext(
        "promtext",
        "--label",
        "first=new",
        "--label",
        "second=new",
        str(promfile),
        "existing_metric",
        "42",
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{first="existing",second="existing"} 0.0'
        "\n"
        'existing_metric{first="new",second="new"} 42.0'
        "\n"
    )


def test_existing_metric_overwrite(tmp_path):
    """Does the command overwrite a metric/labelset"""
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="existing"} 0.0'
        "\n",
    )
    with ArgvContext(
        "promtext",
        "--label",
        "testlabel=existing",
        str(promfile),
        "existing_metric",
        "42",
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="existing"} 42.0'
        "\n"
    )


def test_existing_metric_plain(tmp_path):
    """Does the command overwrite a metric without a label?"""
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        "existing_metric 0.0"
        "\n",
    )
    with ArgvContext("promtext", str(promfile), "existing_metric", "42"):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        "existing_metric 42.0"
        "\n"
    )


def test_existing_metric_labeldrop(tmp_path, capsys):
    """Missing labels are not possible, promtext should fail"""
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="existing"} 0.0'
        "\n",
    )

    with (
        ArgvContext("promtext", str(promfile), "existing_metric", "42"),
        pytest.raises(SystemExit) as pytest_wrapped_e,
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{testlabel="existing"} 0.0'
        "\n"
    )  # the content is not changed
    # check that promtext exits correctly
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 1
    captured = capsys.readouterr()
    assert "previously known label 'testlabel' missing, cannot update!" in captured.err


def test_existing_metric_labelchange(tmp_path, capsys):
    """Changing labels are not possible, promtext should fail"""
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{existinglabel="existing"} 0.0'
        "\n",
    )

    with (
        ArgvContext(
            "promtext",
            "--label",
            "newlabel=new",
            str(promfile),
            "existing_metric",
            "42",
        ),
        pytest.raises(SystemExit) as pytest_wrapped_e,
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{existinglabel="existing"} 0.0'
        "\n"
    )  # the content is not changed
    # check that promtext exits correctly
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 1
    captured = capsys.readouterr()
    assert (
        "previously known label 'existinglabel' missing, cannot update!" in captured.err
    )


def test_existing_metric_labeladd(tmp_path, capsys):
    """Adding new labels are not possible, promtext should fail"""
    promfile = tmp_path / "existing_file.prom"
    promfile.write_text(
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{existinglabel="existing"} 0.0'
        "\n",
    )

    with (
        ArgvContext(
            "promtext",
            "--label",
            "existinglabel=existing",
            "--label",
            "newlabel=new",
            str(promfile),
            "existing_metric",
            "42",
        ),
        pytest.raises(SystemExit) as pytest_wrapped_e,
    ):
        promtext_main()
    assert promfile.exists()
    assert promfile.read_text() == (
        "# HELP existing_metric metric appended by promtext-cli"
        "\n"
        "# TYPE existing_metric gauge"
        "\n"
        'existing_metric{existinglabel="existing"} 0.0'
        "\n"
    )  # the content is not changed
    # check that promtext exits correctly
    assert pytest_wrapped_e.type is SystemExit
    assert pytest_wrapped_e.value.code == 1
    captured = capsys.readouterr()
    assert (
        "labelnames for metric existing_metric not the same, cannot update"
        in captured.err
    )


# TODO: Test docs in promtext
# TODO: Test non-gauge-values
