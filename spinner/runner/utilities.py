import os
from functools import partial
from runner.mpi_io.mpi_runner import MPIRunner
import itertools
import pickle
from rich.progress import Progress
from rich import print as rprint
import pandas as pd
import json


def run_benchmarks(config):
    """
    Generate execution matrix from input configuration and run all benchmarks.
    """
    bench_config = json.load(open(config))
    bench_metadata = bench_config["metadata"]
    bench_metadata["start_timestamp"] = str(pd.Timestamp.now())

    # Iterate over settings in bench_config, excluding metadata
    bench_names = [
        bench_name for bench_name in bench_config if bench_name != "metadata"
    ]

    rprint(f"Running benchmarks for {bench_names}")

    # Each benchmark has different parameters, so we must add all outputs to the execution dataframe.
    rprint(bench_config)

    # Get all parameters from each bench
    parameters = list(
        itertools.chain(*[list(bench_config[bench].keys()) for bench in bench_names])
    )

    columns = list(itertools.chain(["name"], parameters, ["time"]))

    execution_df = pd.DataFrame(columns=columns)

    with Progress() as progress:
        # Helper function to update progress
        def _update_progress(progress, task, value=1):
            progress.advance(task, advance=value)

        # Main progress bar
        bench_task = progress.add_task(
            "[cyan]Running benchmarks",
            # TODO calculate total
            total=100,
        )

        progress_callback = partial(_update_progress, progress, bench_task, value=1)

        for bench_name in bench_names:
            rprint(f"Running benchmark {bench_name}")
            progress_callback()

    bench_metadata["end_timestamp"] = str(pd.Timestamp.now())

    rprint(execution_df)
    with open("bench_metadata.pkl", "wb") as f:
        pickle.dump(bench_metadata, f)
