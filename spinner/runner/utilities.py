import os
import pickle
from contextlib import contextmanager
from typing import BinaryIO

import pandas as pd

from spinner.app import SpinnerApp
from spinner.dry_run import dry_run_context
from spinner.runner import InstanceRunner
from spinner.runner.dry_run_runner import DryRunInstanceRunner
from spinner.runner.progress import RunnerProgress
from spinner.schema import SpinnerConfig


class _NoOpProgress:
    """A no-op progress tracker used during dry-run to suppress the progress bar."""

    def step(self) -> None:
        pass


@contextmanager
def _no_progress():
    yield _NoOpProgress()

# ==============================================================================
# PUBLIC FUNCTIONS
# ==============================================================================


def run_benchmarks(
    app: SpinnerApp,
    config: SpinnerConfig,
    output: BinaryIO,
    benchmark: str | None = None,
    **extra,
):
    """
    Generate execution matrix from input configuration and run all benchmarks.
    """
    # Create DataFrame to store benchmark data
    df = pd.DataFrame(
        columns=[
            "name",
            *config.applications.variables,
            "time",
        ]
    )

    # Save initial timestamp and environment variables.
    start_ts = pd.Timestamp.now()
    start_env = config.metadata.capture_environment()

    # Loop through all benchmarks, executing one by one.
    benchmark_items = list(config.benchmarks.items())
    total_jobs = config.num_jobs
    if benchmark is not None:
        selected = config.benchmarks[benchmark]
        if selected is None:
            raise ValueError(f"Benchmark {benchmark!r} is undefined")
        benchmark_items = [(benchmark, selected)]
        total_jobs = (
            config.metadata.runs
            * selected.num_jobs
            * len(selected.application_names(benchmark))
        )

    # Use dry-run context if dry-run mode is enabled
    progress_ctx = _no_progress() if app.dry_run else RunnerProgress(app, config, total=total_jobs)
    with dry_run_context(app, enabled=app.dry_run, verbosity=app.verbosity) as dry_ctx:
        with progress_ctx as progress:
            for benchmark_name, benchmark_data in benchmark_items:
                for application_name in benchmark_data.application_names(benchmark_name):
                    # Choose runner based on dry-run mode
                    if app.dry_run:
                        runner = DryRunInstanceRunner(
                            app,
                            config,
                            benchmark_name=benchmark_name,
                            application_name=application_name,
                            benchmark=benchmark_data,
                            dataframe=df,
                            progress=progress,
                            extra_args=extra,
                            dry_run_context=dry_ctx,
                        )
                    else:
                        runner = InstanceRunner(
                            app,
                            config,
                            benchmark_name=benchmark_name,
                            application_name=application_name,
                            benchmark=benchmark_data,
                            dataframe=df,
                            progress=progress,
                            extra_args=extra,
                        )
                    runner.run()

    # Only print and save results if not in dry-run mode
    if not app.dry_run:
        app.print(df)

        metadata = {
            "hostname": os.uname().nodename,
            "start_ts": start_ts,
            "start_env": start_env,
            "end_ts": pd.Timestamp.now(),
            "end_env": config.metadata.capture_environment(),
            **extra,
        }

        pickle.dump({"config": config, "metadata": metadata, "dataframe": df}, output)
    else:
        # In dry-run mode, log summary of what would have been executed
        app.print("\n[bold yellow]DRY-RUN:[/] Would save results to output file")
        app.print(f"[dim]Output file:[/] {output.name if hasattr(output, 'name') else 'output stream'}")
        app.print(f"[dim]Total commands simulated:[/] {total_jobs}")
