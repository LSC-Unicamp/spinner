import importlib
import os
import pickle

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


def _warn_missing_plot_configuration(app: SpinnerApp, input_file) -> None:
    input_file.seek(0)
    benchmark_data = pickle.load(input_file)
    input_file.seek(0)

    config = benchmark_data.get("config")
    applications = getattr(config, "applications", None)
    if not applications:
        return

    missing = []
    for app_name in applications:
        app_config = applications[app_name]
        if not getattr(app_config, "plot", []):
            missing.append(app_name)

    if not missing:
        return

    missing_names = ", ".join(repr(name) for name in missing)
    app.print(
        "[b yellow]WARNING[/]: Missing plot configuration for benchmark "
        f"application(s): {missing_names}.\n"
        "Export will still generate a notebook (including dataframe preview via "
        "df.head()), but chart generation requires a 'plot' section in the "
        "benchmark file."
    )


# ==============================================================================
# COMMAND-LINE INTERFACE
# ==============================================================================


@group()
@pass_context
@opt("--verbose", "-v", count=True)
def cli(ctx, verbose) -> None:
    """Spinner: Reproducible benchmarks."""
    app = SpinnerApp.get()
    app.verbosity = verbose
    ctx.obj = app


@cli.command()
@pass_obj
@arg("CONFIG", type=File("r"))
@opt("--output", "-o", default="benchdata.pkl", type=File("wb"))
@opt("--benchmark", "-b", default=None, help="Run only one benchmark block by name.")
@opt("--extra-args", "-e", type=ExtraArgs())
def run(app, config, output, benchmark, extra_args) -> None:
    """Run benchmark from configuration file."""
    try:
        config = SpinnerConfig.from_stream(config)
    except ValidationError as errors:
        _print_errors(app, errors)
        raise SystemExit(1)

    if benchmark and config.benchmarks[benchmark] is None:
        app.print(f"[b red]ERROR[/]: Benchmark {benchmark!r} is undefined.")
        raise SystemExit(1)

    if not extra_args:
        extra_args = {}

    spinner.runner.run(app, config, output, benchmark=benchmark, **extra_args)


@cli.command()
@pass_obj
@opt("--input", "-i", default="benchdata.pkl", type=File("rb"))
def export(app, input) -> None:
    """Export benchmark data."""
    path = importlib.resources.files("spinner.exporter") / "reporter.ipynb"
    try:
        _warn_missing_plot_configuration(app, input)
    except Exception:
        input.seek(0)
    try:
        exporter = importlib.import_module("spinner.exporter")
        exporter.run(path, pkl_db_path=os.path.abspath(input.name))
    except (ImportError, RuntimeError) as error:
        app.print(
            "[b red]ERROR[/]: Export requires optional Jupyter dependencies.\n"
            "Install them with 'pip install spinner[exporter]'."
        )
        raise SystemExit(1) from error


def main():
    cli()


if __name__ == "__main__":
    cli()
