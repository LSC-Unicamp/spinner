"""Dry-run implementation of InstanceRunner.

This module provides a specialized runner that simulates command execution
without actually running commands, providing detailed logging of what would happen.
"""

import subprocess as sp
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
        simulated_returncode = 0
        simulated_elapsed = 0.001  # Simulate very fast execution
        simulated_timed_out = False
        
        # Log expected results
        self.dry_run_context.log_expected_result(
            stdout=simulated_stdout,
            stderr=simulated_stderr,
            returncode=simulated_returncode,
            elapsed=simulated_elapsed,
        )
        
        # Simulate output processing
        if simulated_returncode == 0 and not simulated_timed_out:
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
            
            # In dry-run mode, we don't actually add to dataframe
            # Logging disabled for cleaner output
            # self.app.vprint(
            #     f"[DRY-RUN] Would add row to dataframe: {row_data}"
            # )
        else:
            self.app.warning(
                f"[DRY-RUN] Command would fail with return code {simulated_returncode}"
            )
        
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
            self.dry_run_context.log_capture(key, value)
        
        return captures
    
    def launch_process_with_retry(
        self,
        command: str,
        timeout: float | None = None,
        retry: int | None = None,
    ) -> tuple[str, str, int, float, bool]:
        """Override to prevent actual process execution in dry-run mode.
        
        This method should not be called in dry-run mode, but we override it
        for safety to ensure no actual commands are executed.
        
        Args:
            command: Command string
            timeout: Timeout value
            retry: Retry count
            
        Returns:
            Simulated process results
        """
        self.app.warning(
            "[DRY-RUN] launch_process_with_retry called - "
            "returning simulated results"
        )
        return ("[simulated stdout]", "", 0, 0.001, False)
    
    def execute_process_with_timeout(
        self, command: str, timeout: float | None = None
    ) -> tuple[sp.Popen, float]:
        """Override to prevent actual process execution in dry-run mode.
        
        This method should not be called in dry-run mode, but we override it
        for safety to ensure no actual commands are executed.
        
        Args:
            command: Command string
            timeout: Timeout value
            
        Returns:
            Simulated process and elapsed time
        """
        self.app.warning(
            "[DRY-RUN] execute_process_with_timeout called - "
            "this should not happen in dry-run mode"
        )
        # Return a mock object that won't actually execute anything
        raise RuntimeError(
            "Attempted to execute process in dry-run mode. "
            "This is a safety check to prevent actual execution."
        )


