import importlib
import os

from click import File
from click import argument as arg
from click import group
from click import option as opt
from click import pass_context, pass_obj

import spinner
from spinner.app import SpinnerApp

# ==============================================================================
# COMMAND-LINE INTERFACE
# ==============================================================================


@group()
@pass_context
@opt("--verbose", "-v", count=True)
def cli(ctx, verbose) -> None:
    """Spinner: Reproducible benchmarks."""
    app = SpinnerApp.get()
    app.verbose = verbose
    ctx.obj = app


@cli.command()
@pass_obj
@arg("CONFIG", type=File("r"))
@opt("--hosts", "-h", default=None, type=str, help="Host names")
def run(app, config, hosts) -> None:
    """Run benchmark from configuration file."""
    spinner.runner.run(config, hosts)


@cli.command()
@pass_obj
def export(app) -> None:
    """Export benchmark data."""
    path = importlib.resources.files("spinner.exporter") / "reporter.ipynb"
    spinner.exporter.run(path, "report.html", pkl_db_path=os.getcwd())


def main():
    cli()


if __name__ == "__main__":
    cli()
