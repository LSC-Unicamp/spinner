import logging
from pathlib import Path

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


def test_cli_run_invalid_benchmark_name():
    runner = CliRunner()
    with runner.isolated_filesystem():
        cfg = Path("bench.yaml")
        cfg.write_text(
            """
metadata:
  description: test
  version: "1.0"
  runs: 1
applications:
  app1:
    command: echo run
benchmarks:
  bench_1:
    apps: [app1]
    x: [1]
"""
        )
        result = runner.invoke(cli, ["run", str(cfg), "-b", "bench_missing"])
        assert result.exit_code == 1
        assert "is undefined" in result.output
