import io
import logging
import pickle

import pytest

from spinner.app import SpinnerApp
from spinner.runner import run
from spinner.schema import SpinnerConfig


def test_timeout_triggers_retry(monkeypatch, caplog):
    data = {
        "metadata": {
            "description": "timeout retry",
            "version": "1.0",
            "runs": 1,
            "timeout": 0.1,
            "retry": 2,
            "envvars": [],
            "success_on_return": [-1],
        },
        "applications": {"sleep": {"command": "sleep 1"}},
        "benchmarks": {"sleep": {}},
    }
    config = SpinnerConfig.from_data(data)
    app = SpinnerApp.get()
    app.verbosity = 2
    app.logger.setLevel(logging.INFO)
    caplog.set_level(logging.INFO)
    buf = io.BytesIO()
    run(app, config, buf)
    assert "Retrying" in caplog.text
    buf.seek(0)
    df = pickle.load(buf)["dataframe"]
    assert df.empty
