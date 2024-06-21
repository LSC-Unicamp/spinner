import click
from rich import print as rprint
import os
from runner.utilities import run_benchmarks
from runner.instance_builder import build_all
from exporter.exporter import run_reporter
from generator.rand_int import generate_random_numbers_file as generate_rand_file


@click.command()
@click.option(
    "--config",
    "-c",
    default="bench_settings.json",
    type=str,
    help="Benchmark configuration file",
)
@click.option("--build", "-b", default=False, type=bool, help="Build all benchmarks")
@click.option("--gen", "-g", default=False, type=bool, help="Generate input files")
@click.option("--gensize", "-s", default=None, type=int, help="Gerated input file size")
@click.option("--output", "-o", default=None, type=str, help="Output file")
@click.option("--run", "-r", default=False, type=bool, help="Run all benchmarks")
@click.option(
    "--export", "-e", default=True, type=bool, help="Export results to report.html"
)
@click.option("--hosts", "-h", default=None, type=str, help="Hosts list")
def cli(build, run, export, config, gen, gensize, output, hosts):
    main(build, run, export, config, gen, gensize, output, hosts)


def main(build, run, export, config, gen, gensize, output_file, hosts):
    if gen:
        if not gensize:
            print("Please provide a size for the generated file")
            exit(1)
        if not output_file:
            print("Please provide an output file")
            exit(1)
        generate_rand_file(gensize, output_file)

    if build:
        build_all(config)

    if run:
        run_benchmarks(config, hosts)

    if export:
        reporter_notebook_path = os.path.abspath("spinner/reporter.ipynb")
        run_reporter(reporter_notebook_path, "report.html")


if __name__ == "__main__":
    cli()
