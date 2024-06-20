import subprocess
import os
import signal
from rich.progress import Progress
from rich import print as rprint
import pandas as pd
import time


class ExerciseRunner:
    """
    Base class to handle the general case execution of exercises.

    Attributes:
        execution_df (DataFrame): Data frame containing execution details.
        repos_path (str): Path to the repositories.
        exercise_name (str): Name of the exercise.
        n_runs (int): Number of runs to execute (default is 5).
        run_env (str, optional): The environment in which to run the exercises.
    """

    def __init__(
        self,
        execution_df,
        repos_path,
        exercise_name,
        n_runs=5,
        run_env=None,
    ):
        self.repos_path = repos_path
        self.exercise_name = exercise_name
        self.n_runs = n_runs
        self.execution_df = execution_df
        self.run_env = run_env

    def get_run_instruction(self):
        assert False, "Not implemented by subclass"

    def check_output(self, outputs):
        assert False, "Not implemented by subclass"

    def run_command(self, cmd, timeout=60):
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
            stdout, stderr = process.communicate(timeout=timeout)
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

        if cmd["type"] == "serial":
            assert returncode == 0, f"Non-zero exit code in serial run: {returncode}"

        return (
            stdout,
            stderr,
            elapsed_time,
            returncode,
        )

    def run(self, timeout=60, progress_callback=None):
        """Runs the exercise and stores the results in self.results"""
        run_cmds = self.get_run_instruction()
        df = self.execution_df

        # Separate serial and parallel commands
        serial_cmds = [cmd for cmd in run_cmds if cmd["type"] == "serial"]
        if not self.run_serial:
            serial_cmds = []
        parallel_cmds = [cmd for cmd in run_cmds if cmd["type"] == "parallel"]

        # Run serial commands first (so we can calculate speedup)
        for cmd in serial_cmds + parallel_cmds:
            cmd_failed = False

            for i in range(self.n_runs):
                if progress_callback:
                    progress_callback(1 / len(serial_cmds + parallel_cmds))

                rprint(f"Run {i+1}/{self.n_runs}")
                curr_df_entry = {
                    "student_name": self.student_name,
                    "student_repo": self.student_repo,
                    "exercise_name": self.exercise_name,
                    "instance": cmd["instance"],
                    "output": None,
                    "type": cmd["type"],
                    "time": None,
                    "speedup": None,
                    "reason": None,
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

                curr_df_entry["output"] = output

                # If not serial, calculate speedup
                if cmd["type"] == "parallel":
                    curr_df_entry["speedup"] = self.get_speedup(
                        cmd, elapsed_time, output
                    )
                else:
                    curr_df_entry["speedup"] = 1.0

                # Append run to execution_df
                curr_df_entry["time"] = elapsed_time
                df.loc[len(df)] = curr_df_entry
