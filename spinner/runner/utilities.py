import os
import pickle
from pathlib import Path

import pandas as pd

from spinner.app import SpinnerApp
from spinner.runner import InstanceRunner
from spinner.runner.progress import RunnerProgress
from spinner.schema import SpinnerConfig

# ==============================================================================
# PUBLIC FUNCTIONS
# ==============================================================================


def run_benchmarks(app: SpinnerApp, config: SpinnerConfig):
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
    start_env = os.environ.copy()

    # Loop through all benchmarks, executing one by one.
    with RunnerProgress(app, config) as progress:
        for name, bench in config.benchmarks.items():
            runner = InstanceRunner(
                app,
                config,
                name=name,
                benchmark=bench,
                dataframe=df,
                progress=progress,
            )
            runner.run()

    app.print(df)

    metadata = {
        "hostname": os.uname().nodename,
        "start_ts": start_ts,
        "start_env": start_env,
        "end_ts": pd.Timestamp.now(),
        "end_env": os.environ.copy(),
    }

    with Path("bench_metadata.pkl").open(mode="wb") as f:
        pickle.dump({"config": config, "metadata": metadata, "dataframe": df}, f)
