from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from spinner.app import SpinnerApp
from spinner.schema import SpinnerConfig


class RunnerProgress(Progress):
    task: int

    def __init__(self, app: SpinnerApp, config: SpinnerConfig, *args, **kwargs) -> None:
        super().__init__(
            SpinnerColumn("point"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=app,
            **kwargs,
        )
        self.task = self.add_task("Running Benchmarks", total=config.num_jobs)

    def step(self) -> None:
        self.advance(self.task)
