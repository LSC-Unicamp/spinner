import importlib.resources
import os

import click

import spinner


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
    if run:
        spinner.runnner.run(config, hosts)

    if export:
        path = importlib.resources.files("spinner.exporter") / "reporter.ipynb"
        spinner.exporter.run(path, "report.html", pkl_db_path=os.getcwd())


def main():
    cli()


if __name__ == "__main__":
    cli()
