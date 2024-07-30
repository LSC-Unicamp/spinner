import os
from functools import partial
from runner.mpi_io.mpi_runner import MPIRunner
from runner.omp_tasks.omp_runner import OmpRunner
import itertools
import pickle
from rich.progress import Progress
from rich import print as rprint
import pandas as pd
import json


def run_benchmarks(config, hosts):
    """
    Generate execution matrix from input configuration and run all benchmarks.
    """
    bench_config = json.load(open(config))
    bench_metadata = bench_config["metadata"]
    bench_metadata["start_timestamp"] = str(pd.Timestamp.now())

    input_file = bench_metadata["input_file"]
    input_file_size = os.path.getsize(input_file)

    bench_metadata["input_file_size"] = input_file_size
    bench_metadata["hosts"] = hosts
    bench_metadata["runner_hostname"] = str(os.uname()[1])
    bench_metadata["start_env"] = str(os.environ.copy())

    # TODO: include lfs getstripe in metadata as well

    # Iterate over settings in bench_config, excluding metadata
    bench_names = [
        bench_name for bench_name in bench_config if bench_name != "metadata"
    ]

    # rprint(f"Running benchmarks for {bench_names}")

    # Each benchmark has different parameters, so we must add all outputs to the execution dataframe.
    # rprint(bench_config)

    # Get all parameters from each bench
    parameters = list(
        itertools.chain(*[list(bench_config[bench].keys()) for bench in bench_names])
    )

    columns = list(itertools.chain(["name"], parameters, ["time"]))

    execution_df = pd.DataFrame(columns=columns)

    # TODO: move this somewhere else
    bench_runners = {
        "mpi-io": MPIRunner,
        "omp-tasks": OmpRunner,
    }

    with Progress() as progress:
        # Helper function to update progress
        def _update_progress(
            progress, task, value=None, total=None, increment_total=None
        ):
            if total is not None:
                progress.update(task, total=total)
            if value is not None:
                progress.advance(task, advance=value)
            if increment_total is not None:
                progress.update(
                    task, total=progress.tasks[task].total + increment_total
                )

        # Main progress bar
        bench_task = progress.add_task(
            "[cyan]Running benchmarks",
        )

        # Handle to progress bar updates
        progress_callback = partial(
            _update_progress,
            progress,
            bench_task,
            value=None,
            total=None,
            increment_total=None,
        )

        for bench_name in bench_names:
            if bench_name not in bench_runners:
                rprint(f"[red]WARNING: runner for {bench_name} not found")
                continue

            instance_runner = bench_runners[bench_name](
                execution_df,
                bench_config["metadata"],
                bench_config[bench_name],
                progress_callback,
            )

            instance_runner.run()

            progress_callback()

    bench_metadata["end_timestamp"] = str(pd.Timestamp.now())
    bench_metadata["end_env"] = str(os.environ.copy())

    rprint(execution_df)
    with open("bench_metadata.pkl", "wb") as f:
        pickle.dump({"metadata": bench_metadata, "dataframe": execution_df}, f)
