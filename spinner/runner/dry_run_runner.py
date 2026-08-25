from typing import Any

from spinner.app import SpinnerApp
from spinner.dry_run import DryRunContext
from spinner.runner.instance_runner import InstanceRunner
from spinner.schema import SpinnerBenchmark, SpinnerConfig


class DryRunInstanceRunner(InstanceRunner):
    def __init__(
        self,
        app: SpinnerApp,
        config: SpinnerConfig,
        *,
        benchmark_name: str,
        application_name: str,
        benchmark: SpinnerBenchmark,
        dataframe,
        progress,
        extra_args: dict[str, str] | None = None,
        dry_run_context: DryRunContext | None = None,
    ) -> None:
        super().__init__(
            app,
            config,
            benchmark_name=benchmark_name,
            application_name=application_name,
            benchmark=benchmark,
            dataframe=dataframe,
            progress=progress,
            extra_args=extra_args,
        )
        self.dry_run_context = dry_run_context or DryRunContext(app, enabled=True, verbosity=app.verbosity)

    def run_command(
        self,
        idx: int,
        command: str,
        parameters: dict[str, Any],
        *,
        timeout: float | None = None,
        retry: int | None = None,
    ) -> None:
        self.dry_run_context.log_command(
            command=command,
            parameters=parameters,
            timeout=timeout,
            retry=retry,
            app_name=self.application_name,
            benchmark_name=self.benchmark_name,
        )

        self.dry_run_context.log_expected_result(
            stdout=f"[Simulated output for: {command}]",
            elapsed=0.001,
        )
        self.progress.step()
