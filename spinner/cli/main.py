import importlib.resources
import os

import click
import exporter.exporter as exporter
from runner.utilities import run_benchmarks


@click.command()
@click.option(
    "--config",
    "-c",
    default="bench_settings.json",
    type=str,
    help="Benchmark configuration file",
)
@click.option("--run", "-r", default=False, type=bool, help="Run all benchmarks")
@click.option(
    "--export", "-e", default=True, type=bool, help="Export results to report.html"
)
@click.option("--hosts", "-h", default=None, type=str, help="Hosts list")
def cli(run, export, config, hosts):
    main(run, export, config, hosts)


def main(run, export, config, hosts):
    if run:
        run_benchmarks(config, hosts)

    if export:
        reporter_path = importlib.resources.files("exporter") / "reporter.ipynb"
        exporter.run_reporter(reporter_path, "report.html", pkl_db_path=os.getcwd())


if __name__ == "__main__":
    cli()
