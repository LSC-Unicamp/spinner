import importlib
import os

from click import File
from click import argument as arg
from click import group
from click import option as opt
from click import pass_context, pass_obj
from pydantic import ValidationError

import spinner
from spinner.app import SpinnerApp
from spinner.schema import SpinnerConfig

from .util import ExtraArgs

# ==============================================================================
# LOCAL FUNCTIONS
# ==============================================================================


def _print_errors(app: SpinnerApp, exception: ValidationError) -> None:
    n = len(exception.errors())
    app.print(f"[b red]ERROR[/]: Invalid configuration file ({n} errors)")

    for i, error in enumerate(exception.errors(), start=1):
        path = ".".join([str(x) for x in error.get("loc")])
        message = error.get("msg")
        app.print(f"\n{i:3}. Error in [i]{path!r}[/]\n     [dim]{message}[/]")

    app.print("\nPlease fix the above errors and try again.")


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
@opt("--output", "-o", default="benchdata.pkl", type=File("wb"))
@opt("--extra-args", "-e", type=ExtraArgs())
def run(app, config, output, extra_args) -> None:
    """Run benchmark from configuration file."""
    try:
        config = SpinnerConfig.from_stream(config)
    except ValidationError as errors:
        _print_errors(app, errors)
        raise SystemExit(1)

    if not extra_args:
        extra_args = {}

    spinner.runner.run(app, config, output, **extra_args)


@cli.command()
@pass_obj
@opt("--input", "-i", default="benchdata.pkl", type=File("rb"))
def export(app, input) -> None:
    """Export benchmark data."""
    path = importlib.resources.files("spinner.exporter") / "reporter.ipynb"
    spinner.exporter.run(path, "report.html", pkl_db_path=os.path.abspath(input.name))


def main():
    cli()


if __name__ == "__main__":
    cli()
