import logging
from click.testing import CliRunner

from spinner.cli.main import cli
from spinner.app import SpinnerApp


def test_cli_verbose_sets_logger(monkeypatch):
    app = SpinnerApp.get()
    app.logger.setLevel(logging.WARNING)
    app.verbosity = 0
    runner = CliRunner()
    result = runner.invoke(cli, ['-vv', 'export', '--help'])
    assert result.exit_code == 0
    assert app.verbosity == 2
    assert app.logger.level == logging.INFO


def test_cli_log_level_env(monkeypatch):
    app = SpinnerApp.get()
    app.logger.setLevel(logging.WARNING)
    app.verbosity = 0
    monkeypatch.setenv('LOGLEVEL', 'INFO')
    runner = CliRunner()
    result = runner.invoke(cli, ['export', '--help'])
    assert result.exit_code == 0
    assert app.verbosity == 0
    assert app.logger.level == logging.INFO

