import click
from rich import print as rprint
from runner.utilities import run_benchmarks


@click.command()
@click.option(
    "--config",
    "-c",
    default="bench_settings.json",
    type=str,
    help="Benchmark configuration file",
)
@click.option("--build", "-b", default=True, type=bool, help="Build all benchmarks")
@click.option("--run", "-r", default=True, type=bool, help="Run all benchmarks")
@click.option(
    "--export", "-e", default=True, type=bool, help="Export results to report.html"
)
def cli(build, run, export, config):
    main(build, run, export, config)


def main(build, run, export, config):
    if build:
        assert False, "Not implemented"

    if run:
        run_benchmarks(config)

    if export:
        assert False, "Not implemented"


if __name__ == "__main__":
    cli()
