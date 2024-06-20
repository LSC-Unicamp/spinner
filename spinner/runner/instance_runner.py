import subprocess
import os
import signal
from rich.progress import Progress
from rich import print as rprint
import pandas as pd
import time


class InstanceRunner:
    """
    Base class to handle the general case execution of benchmarks.
    """

    def __init__(
        self,
        execution_df,
        metadata,
        config,
        progress_callback,
    ):
        self.execution_df = execution_df
        self.metadata = metadata
        self.config = config
        self.progress_callback = progress_callback

    def get_run_instruction(self):
        assert False, "Not implemented by subclass"

    def check_output(self, outputs):
        assert False, "Not implemented by subclass"

    def run_command(self, cmd, timeout):
        """Runs a command and returns the output, time and return code"""
        cwd = os.path.join(self.repos_path, self.student_repo, self.exercise_name)
        cwd = os.path.abspath(cwd)

        rprint(f" -> Running {cmd['command']}\n     in: {cwd}")

        start_time = time.time()

        try:
            process = subprocess.Popen(
                cmd["command"],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                env=self.run_env,
            )
            stdout, stderr = process.communicate(timeout)
            returncode = process.returncode
            stderr = stderr.decode()
            stdout = stdout.decode()

        except subprocess.TimeoutExpired as e:
            rprint(f" -> Command timeout after {timeout} seconds")
            process.kill()
            process.communicate()
            returncode = -1  # Typically, -1 indicates a timeout error
            stderr = f"Timeout error (limit: {timeout}s)"
            stdout = ""
            rprint(f" -> Killing children group {process.pid}")
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except ProcessLookupError:
                rprint(
                    f" -> Failed to kill children group {process.pid}, probably already dead"
                )
            rprint(f" -> Done killing children group {process.pid}")

        end_time = time.time()
        elapsed_time = end_time - start_time
        rprint(f"-> stderr = {stderr}")
        rprint(f"-> stdout = {stdout}")
        rprint(f"-> elapsed time = {elapsed_time}")
        rprint(f"-> return code = {returncode}")

        return (
            stdout,
            stderr,
            elapsed_time,
            returncode,
        )

    def run(self):
        """Runs the exercise and stores the results in self.results"""
        run_cmds = self.get_run_instruction()

        # Run serial commands first (so we can calculate speedup)
        for cmd in run_cmds:
            rprint(self.config)
            rprint(self.metadata)
            for i in range(self.metadata["runs"]):
                self.progress_callback(1 / len(run_cmds))

                rprint(f"Run {i+1}/{self.n_runs}")
                curr_df_entry = {
                    "name": self.get_bench_name(),
                    **cmd["parameters"],
                }

                if not self.assert_binary(cmd["command"]):
                    rprint(f"-> Failed to compile {cmd['command']}")
                    curr_df_entry["reason"] = "Failed to compile"
                    df.loc[len(df)] = curr_df_entry
                    continue

                if cmd_failed:
                    rprint(f"-> Skipping command: {cmd['command']}")
                    rprint(f"-> Previous execution failed")
                    continue

                output, error, elapsed_time, return_code = self.run_command(
                    cmd, timeout=timeout
                )

                if not return_code == 0:
                    rprint(f"-> Error running command: {cmd['command']}\n{error}")
                    curr_df_entry["reason"] = "Non-zero exit code"
                    df.loc[len(df)] = curr_df_entry

                    cmd_failed = True
                    continue

                if not self.check_output(output, cmd):
                    rprint(f"-> Output incorrect: {output}")
                    curr_df_entry["reason"] = "Incorrect output"
                    df.loc[len(df)] = curr_df_entry
                    cmd_failed = True
                    continue

                # Append run to execution_df
                curr_df_entry["time"] = elapsed_time
                df.loc[len(df)] = curr_df_entry
