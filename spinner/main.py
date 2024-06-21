import click
from rich import print as rprint
from runner.utilities import run_benchmarks
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
@click.option("--run", "-r", default=True, type=bool, help="Run all benchmarks")
@click.option(
    "--export", "-e", default=True, type=bool, help="Export results to report.html"
)
def cli(build, run, export, config, gen, gensize, output):
    main(build, run, export, config, gen, gensize, output)


def main(build, run, export, config, gen, gensize, output_file):
    if gen:
        if not gensize:
            print("Please provide a size for the generated file")
            exit(1)
        if not output_file:
            print("Please provide an output file")
            exit(1)
        generate_rand_file(gensize, output_file)
        exit(0)

    if build:
        assert False, "Not implemented"

    if run:
        run_benchmarks(config)

    if export:
        assert False, "Not implemented"


if __name__ == "__main__":
    cli()
