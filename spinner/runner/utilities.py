import os
from functools import partial
from rich.progress import Progress
from rich import print as rprint
import pandas as pd
import json


def run_benchmarks(config):
    """
    Generate execution matrix from input configuration and run all benchmarks.
    """
    rprint(f"Reading configuration from {config}")
    bench_config = json.load(open(config))
    rprint(bench_config)
    bench_metadata = bench_config["metadata"]

    exit(0)
    # list repositories in the repos_path
    repos = [
        r
        for r in os.listdir(repos_path)
        if os.path.isdir(os.path.join(repos_path, r)) and not r.startswith(".")
    ]

    repos = sorted(repos)
    if repo_list:
        repos = [r for r in repos if r in repo_list]
        rprint(f"Warning: Running only repos: {repo_list}")

    assert "base" in repos, "Base repo not found"

    # Move 'base' to the front of the list
    repos.remove("base")
    repos.insert(0, "base")

    # Create execution dataframe with header: Student name, Student repo, exercise name, instance, serial or parallel, time, speedup, reason
    execution_df = pd.DataFrame(
        columns=[
            "student_name",
            "student_repo",
            "exercise_name",
            "instance",
            "output",
            "type",
            "time",
            "speedup",
            "reason",
        ]
    )

    with Progress() as progress:
        # Helper function to update progress
        def _update_progress(progress, tasks, value=1):
            for task in tasks:
                progress.advance(task, advance=value)

        # Main progress bar
        repos_task = progress.add_task(
            "[cyan]Processing benchmarks...",
            # All repos * all exercises * n_runs + serial in base repo
            total=float(len(repos) * len(exercises) * n_runs),
        )

        # Per repo progress bar
        assignments_task = progress.add_task("...")

        for repo_name in repos:
            bar_description = f"[magenta]Running benchmarks in {repo_name}..."

            run_serial = True if repo_name == "base" else False

            progress.reset(
                assignments_task,
                total=float(len(exercises) * n_runs),
                description=bar_description,
            )

            progress_callback = partial(
                _update_progress, progress, [assignments_task, repos_task]
            )

            for exercise in exercises:
                exercise_runner = exercises_runners[exercise]
                exercise_runner(
                    repos_path,
                    student_name="base",
                    n_runs=n_runs,
                ).run(timeout, progress_callback)

    rprint(execution_df)
    execution_df.to_pickle("execution_df.pkl")
