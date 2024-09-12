import importlib
import os

from click import File
from click import argument as arg
from click import group
from click import option as opt

import spinner

# ==============================================================================
# COMMAND-LINE INTERFACE
# ==============================================================================


@group()
def cli() -> None:
    """Spinner: Reproducible benchmarks."""
    pass


@cli.command()
@arg("CONFIG", type=File("r"))
@opt("--hosts", "-h", default=None, type=str, help="Host names")
def run(config, hosts) -> None:
    """Run benchmark from configuration file."""
    spinner.runner.run(config, hosts)


@cli.command()
def export() -> None:
    """Export benchmark data."""
    path = importlib.resources.files("spinner.exporter") / "reporter.ipynb"
    spinner.exporter.run(path, "report.html", pkl_db_path=os.getcwd())


def main():
    cli()


if __name__ == "__main__":
    cli()
