import importlib
import os

from click import File, group, pass_context, pass_obj
from click import argument as arg
from click import option as opt
from pydantic import ValidationError

import spinner
from spinner.app import SpinnerApp
from spinner.schema import SpinnerConfig

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
    ctx.obj = SpinnerApp(verbosity=verbose)


@cli.command()
@pass_obj
@arg("CONFIG", type=File("r"))
def run(app, config) -> None:
    """Run benchmark from configuration file."""
    try:
        config = SpinnerConfig.from_stream(config)
    except ValidationError as errors:
        _print_errors(app, errors)
        raise SystemExit(1)

    spinner.runner.run(app, config)


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
