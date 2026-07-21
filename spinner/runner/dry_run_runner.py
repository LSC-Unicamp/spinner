"""Dry-run implementation of InstanceRunner.

This module provides a specialized runner that simulates command execution
without actually running commands, providing detailed logging of what would happen.
"""

from typing import Any

from spinner.app import SpinnerApp
from spinner.dry_run import DryRunContext
from spinner.runner.instance_runner import InstanceRunner
from spinner.schema import SpinnerApplication, SpinnerBenchmark, SpinnerConfig


class DryRunInstanceRunner(InstanceRunner):
    """Instance runner that simulates execution in dry-run mode.
    
    This runner logs all operations that would be performed without actually
    executing commands or modifying data.
    """
    
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
        """Initialize dry-run runner.
        
        Args:
            app: SpinnerApp instance
            config: Configuration
            benchmark_name: Name of benchmark
            application_name: Name of application
            benchmark: Benchmark data
            dataframe: DataFrame for results
            progress: Progress tracker
            extra_args: Extra arguments
            dry_run_context: Dry-run context for logging
        """
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
        """Simulate running a command in dry-run mode.
        
        Args:
            idx: Run index
            command: Command to simulate
            parameters: Command parameters
            timeout: Timeout value
            retry: Retry count
        """
        # Log the command that would be executed
        self.dry_run_context.log_command(
            command=command,
            parameters=parameters,
            timeout=timeout,
            retry=retry,
        )
        
        # Simulate successful execution
        simulated_stdout = f"[Simulated output for: {command}]"
        simulated_stderr = ""
        simulated_elapsed = 0.001  # Simulate very fast execution

        # Log expected results
        self.dry_run_context.log_expected_result(
            stdout=simulated_stdout,
            stderr=simulated_stderr,
            elapsed=simulated_elapsed,
        )

        # Simulate output processing
        output = "\n".join([simulated_stdout, simulated_stderr])
        captures = self.process_captures_dry_run(output)

        # Log what would be added to dataframe
        row_data = {
            "name": self.application_name,
            **parameters,
            **captures,
            "time": simulated_elapsed,
        }

        self.dry_run_context.log_dataframe_update(row_data)
        
        # Still update progress to show advancement
        self.progress.step()
    
    def process_captures_dry_run(self, stdout: str) -> dict[str, Any]:
        """Process captures in dry-run mode with logging.
        
        Args:
            stdout: Simulated stdout
            
        Returns:
            Dictionary of captured values
        """
        captures = {}
        for capture in self.application.capture:
            # Simulate capture processing
            key, value = capture.process(stdout)
            
            # For dry-run, use placeholder values
            if value is None:
                value = f"<simulated_{key}>"
            
            captures[key] = value

        return captures


