import os
import pickle
from typing import BinaryIO

import pandas as pd

from spinner.app import SpinnerApp
from spinner.runner import InstanceRunner
from spinner.runner.progress import RunnerProgress
from spinner.schema import SpinnerConfig

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

    with RunnerProgress(app, config, total=total_jobs) as progress:
        for benchmark_name, benchmark_data in benchmark_items:
            for application_name in benchmark_data.application_names(benchmark_name):
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
