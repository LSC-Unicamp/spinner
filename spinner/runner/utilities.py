import os
import pickle
from contextlib import contextmanager
from pathlib import Path
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

def run_benchmarks(
    app: SpinnerApp,
    config: SpinnerConfig,
    output: BinaryIO,
    benchmark: str | None = None,
    **extra,
):
    """Generate execution matrix from input configuration and run all benchmarks."""
    df = pd.DataFrame(
        columns=[
            "name",
            *config.applications.variables,
            "time",
        ]
    )

    start_ts = pd.Timestamp.now()
    start_env = config.metadata.capture_environment()

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

    # Probe writability early so a bad output path fails before any work is done.
    # Only applies to Click LazyFile (_f is None until first write).
    _probe_path: Path | None = None
    _probe_created: bool = False
    if app.dry_run and getattr(output, "_f", True) is None:
        _probe_path = Path(output.name)
        if str(_probe_path) not in ("-", "<stdout>"):
            _probe_created = not _probe_path.exists()
            try:
                _probe_path.open("ab").close()
            except OSError as exc:
                app.print(f"[b red]ERROR[/]: Cannot write output file: {exc.strerror}: {exc.filename}")
                raise SystemExit(1) from exc

    progress_ctx = _no_progress() if app.dry_run else RunnerProgress(app, config, total=total_jobs)
    with dry_run_context(app, enabled=app.dry_run, verbosity=app.verbosity) as dry_ctx:
        if app.dry_run and hasattr(output, "name"):
            dry_ctx.set_output_name(output.name)
        with progress_ctx as progress:
            for benchmark_name, benchmark_data in benchmark_items:
                for application_name in benchmark_data.application_names(benchmark_name):
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
        if _probe_path is not None and _probe_created and _probe_path.exists():
            _probe_path.unlink()
