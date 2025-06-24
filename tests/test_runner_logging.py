import io
import logging
import pickle

import pandas as pd
import pytest

from spinner.app import SpinnerApp
from spinner.runner import run
from spinner.schema import SpinnerConfig


def make_config(command: str) -> SpinnerConfig:
    data = {
        "metadata": {
            "description": "log test",
            "version": "1.0",
            "runs": 1,
            "timeout": 5,
            "retry": 0,
            "envvars": [],
        },
        "applications": {"test": {"command": command}},
        "benchmarks": {"test": {}},
    }
    return SpinnerConfig.from_data(data)


def run_with_verbosity(command: str, verbosity: int, caplog):
    caplog.set_level(logging.DEBUG)
    config = make_config(command)
    app = SpinnerApp.get()
    app.verbosity = verbosity
    level = logging.INFO if verbosity > 0 else logging.WARNING
    app.logger.setLevel(level)
    buf = io.BytesIO()
    run(app, config, buf)
    buf.seek(0)
    return caplog.text, pickle.load(buf)["dataframe"]


def test_no_verbose_hides_command(caplog):
    logs, df = run_with_verbosity("echo hi", 0, caplog)
    assert "run 0: $ echo hi" not in logs
    assert "return code" not in logs
    assert df.empty is False


def test_verbose_shows_command(caplog):
    logs, _ = run_with_verbosity("echo hi", 1, caplog)
    assert "run 0: $ echo hi" in logs
    assert "return code" not in logs


def test_very_verbose_shows_output(caplog):
    logs, _ = run_with_verbosity("echo hi", 2, caplog)
    assert "run 0: $ echo hi" in logs
    assert "hi" in logs
    assert "return code: 0" in logs


def test_invalid_command_logged(caplog):
    logs, df = run_with_verbosity("command-does-not-exist", 2, caplog)
    assert "Failed to run command." in logs
    assert df.empty
