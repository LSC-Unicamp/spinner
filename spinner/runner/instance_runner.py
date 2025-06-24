import subprocess as sp
import time
from typing import Any

import pandas as pd
from jinja2 import Environment, Undefined
from jinja2.exceptions import UndefinedError

from spinner.app import SpinnerApp
from spinner.runner.progress import RunnerProgress
from spinner.schema import SpinnerApplication, SpinnerBenchmark, SpinnerConfig


class StrictUndefined(Undefined):
    def __getattr__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __getitem__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __str__(self):
        raise NameError(f"'{self._undefined_name}' is undefined")


class InstanceRunner:
    """Base class to handle the general case execution of benchmarks."""

    app: SpinnerApp
    config: SpinnerConfig
    name: str
    benchmark: SpinnerBenchmark
    dataframe: pd.DataFrame
    application: SpinnerApplication
    extra_args: dict[str, str] | None

    def __init__(
        self,
        app: SpinnerApp,
        config: SpinnerConfig,
        *,
        name: str,
        benchmark: SpinnerBenchmark,
        dataframe: pd.DataFrame,
        progress: RunnerProgress,
        extra_args: dict[str, str] | None = None,
    ) -> None:
        self.app = app
        self.config = config
        self.name = name
        self.benchmark = benchmark
        self.dataframe = dataframe
        self.progress = progress
        self.application = config.applications[name]
        self.environment = Environment(undefined=StrictUndefined)
        self.extra_args = extra_args

    def run(self) -> None:
        """Sweep the benchmark parameters and execute each combination."""
        for parameters in self.benchmark.sweep_parameters(self.extra_args):
            self.run_with_parameters(parameters)

    def run_with_parameters(self, parameters: dict[str, Any]) -> None:
        """Run benchmark with a single combination of parameters."""
        timeout = self.config.metadata.timeout
        retry = self.config.metadata.retry

        try:
            command = self.application.render(self.environment, **parameters)
        except UndefinedError as e:
            self.app.fatal(f"Application {self.name}: {e}.")
            return

        # Run the command once, for each run.
        for i in range(self.config.metadata.runs):
            self.run_command(
                i, command, parameters, timeout=timeout, retry=retry
            )

    def run_command(
        self,
        idx: int,
        command: str,
        parameters: dict[str, Any],
        *,
        timeout: float | None = None,
        retry: int | None = None,
    ) -> None:
        """Run a command and capture its output."""
        self.app.vprint(f"run {idx}: $ {command}")
        stdout, stderr, retcode, elapsed, timed_out = self.launch_process_with_retry(
            command, timeout, retry
        )

        self.app.vvprint(stdout)
        self.app.vvprint(stderr)
        self.app.vvprint(f"return code: {retcode}")

        if timed_out or not self.config.metadata.is_success(retcode):
            self.app.error("Failed to run command.")
            return

        output = "\n".join([stdout, stderr])
        captures = self.process_captures(output)

        self.dataframe.loc[len(self.dataframe)] = {
            "name": self.name,
            **parameters,
            **captures,
            "time": elapsed,
        }

        self.progress.step()

    def launch_process_with_retry(
        self,
        command: str,
        timeout: float | None = None,
        retry: int | None = None,
    ) -> tuple[str, str, int, float, bool]:
        """Launch a process, retrying in case of failure."""
        remaining_tries = retry or 1
        attempt = 0

        while remaining_tries > 0:
            attempt += 1
            timed_out = False
            try:
                process, elapsed = self.execute_process_with_timeout(command, timeout)
                stdout = process.stdout
                stderr = process.stderr
                returncode = process.returncode
            except sp.TimeoutExpired:
                timed_out = True
                stdout = ""
                stderr = f"Timeout error: (limit: {timeout}s)"
                returncode = -1
                elapsed = float(timeout)

            success = self.config.metadata.is_success(returncode)
            if success and not timed_out:
                break

            remaining_tries -= 1
            if remaining_tries > 0:
                self.app.vprint(
                    f"Attempt {attempt} failed with code {returncode}. Retrying..."
                )
            else:
                self.app.error(
                    f"Attempt {attempt} failed with code {returncode}. No retries left."
                )

        return (stdout, stderr, returncode, elapsed, timed_out)

    def execute_process_with_timeout(
        self, command: str, timeout: float | None = None
    ) -> tuple[sp.Popen, float]:
        """Execute a process and wait for it to finish or reach the timeout."""
        t = time.monotonic()

        process = sp.Popen(
            command,
            shell=True,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            start_new_session=True,
            text=True,
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            process.stdout = stdout
            process.stderr = stderr
        except sp.TimeoutExpired as err:
            process.kill()
            raise err

        elapsed = time.monotonic() - t
        return process, elapsed

    def process_captures(self, stdout: str) -> dict[str, str]:
        captures = {}
        for capture in self.application.capture:
            key, value = capture.process(stdout)
            captures[key] = value
        return captures
