import itertools
import os
import signal
import subprocess
import time

from jinja2 import Environment, Undefined
from rich import print as rprint


class StrictUndefined(Undefined):
    def __getattr__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __getitem__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __str__(self):
        raise NameError(f"'{self._undefined_name}' is undefined")


class InstanceRunner:
    """
    Base class to handle the general case execution of benchmarks.
    """

    def __init__(
        self,
        bench_name,
        execution_df,
        metadata,
        sweep_parameters,
        progress_callback,
        runner_env=None,
    ):
        self.bench_name = bench_name
        self.execution_df = execution_df
        self.metadata = metadata
        self.sweep_parameters = sweep_parameters
        self.progress_callback = progress_callback
        self.runner_env = runner_env

    def get_parameter_combinations(self):
        parameter_list = self.sweep_parameters.keys()
        parameter_combinations = list(
            itertools.product(
                *[self.sweep_parameters[param] for param in parameter_list]
            )
        )
        parameter_combinations = (
            dict(zip(parameter_list, comb)) for comb in parameter_combinations
        )

        return parameter_combinations

    def get_run_instruction(self) -> list:
        instructions = []

        parameter_combinations = self.get_parameter_combinations()

        for parameters in list(parameter_combinations):
            rprint(f"self.metadata: {self.metadata}")
            command_info = self.metadata[self.bench_name]["command"]
            template_string = command_info["template"]
            rprint(f"command_template: {template_string}")

            env = Environment(undefined=StrictUndefined)
            template = env.from_string(template_string)

            command = template.render(
                self.metadata | parameters | self.metadata[self.bench_name]
            )
            rprint(f"rendered command: {command}")

            instructions.append(
                {
                    "cmd": command,
                    "parameters": parameters,
                }
            )

        return instructions

    def check_output(self, output) -> bool:
        # TODO check the output
        rprint("[red] Check output not implemented!")
        return True

    def filter_output(self, output, error, output_filter):
        combined_output = str(output + error)
        filtered_output = ""
        captured_parameters = {}

        for filter in output_filter:
            current_capture = ""

            if filter["type"] == "all":
                current_capture = combined_output

            elif filter["type"] == "contains":
                rprint(f"-> Filtering lines that contain: {filter['pattern']}")
                current_capture += "\n".join(
                    [
                        line
                        for line in combined_output.split("\n")
                        if filter["pattern"] in line
                    ]
                )
                current_capture += "\n"

            else:
                rprint(f"[red] Unsupported filter type: {filter['type']}")

            if "to_float" in filter:
                rprint("-> Converting captured line to float")
                param_name = filter["to_float"]["name"]
                param_lambda = filter["to_float"]["lambda"]

                try:
                    param_value = eval(param_lambda, {}, {})(current_capture)
                except Exception as e:
                    rprint(f"-> Error evaluating param_lambda: {e}")
                    param_value = None

                captured_parameters[param_name] = param_value

            filtered_output += current_capture

        rprint(f"-> Filtered output: {filtered_output}")
        rprint(f"-> Captured parameters: {captured_parameters}")

        return str(filtered_output), captured_parameters

    def run(self):
        """Runs the exercise and stores the results in self.results"""
        run_cmds = self.get_run_instruction()
        self.progress_callback(increment_total=(len(run_cmds) * self.metadata["runs"]))

        for cmd in run_cmds:
            for i in range(self.metadata["runs"]):
                self.progress_callback(value=1)

                curr_df_entry = {
                    "name": self.bench_name,
                    **cmd["parameters"],
                    "time": None,
                }

                rprint(curr_df_entry)

                output, error, elapsed_time, return_code = self.run_command(
                    cmd,
                    self.metadata["timeout"],
                    self.metadata["retry"],
                    self.metadata["retry_limit"],
                )

                if not return_code == 0:
                    rprint(f"-> Error running command: {cmd['cmd']}\n{error}")
                    continue

                if not self.check_output(output):
                    rprint(f"-> Output incorrect: {output}")
                    continue

                # Append run to execution_df
                curr_df_entry["time"] = elapsed_time
                if "output" in self.metadata[self.bench_name]:
                    rprint("-> Capturing output")
                    filtered_output, captured_parameters = self.filter_output(
                        output, error, self.metadata[self.bench_name]["output"]
                    )

                    curr_df_entry["output"] = filtered_output
                    for param_name, param_value in captured_parameters.items():
                        curr_df_entry[param_name] = param_value

                if not set(curr_df_entry.keys()).issubset(
                    set(self.execution_df.columns)
                ):
                    raise ValueError(
                        "Entry contains a column that is mising in the dataframe."
                    )
                self.execution_df.loc[len(self.execution_df)] = curr_df_entry

    def run_command(self, cmd, timeout: int, retry: bool, retry_limit: int):
        """Runs a command and returns the output, time and return code"""
        rprint(f"-> Running command: {cmd['cmd']}")
        rprint(f"-> Path: {os.getcwd()}")
        rprint(f"-> Timeout: {timeout}")

        # Retry logic to run until success
        remaining_tries = 1
        if retry and retry_limit > 0:
            remaining_tries = retry_limit
            rprint(f"-> Retry enabled with limit {retry_limit}")
        elif retry and retry_limit <= 0:
            remaining_tries = float("inf")
            rprint("-> Retry enabled without limit")
        else:
            remaining_tries = 1
            rprint("-> Retry disabled")

        finished = False
        while remaining_tries > 0 and not finished:
            remaining_tries -= 1
            start_time = time.time()
            try:
                process = subprocess.Popen(
                    cmd["cmd"],
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    # cwd=cwd,
                    env=self.runner_env,
                    start_new_session=True,
                )
                stdout, stderr = process.communicate(timeout=timeout)
                returncode = process.returncode
                stderr = stderr.decode()
                stdout = stdout.decode()
                finished = True

            except subprocess.TimeoutExpired:
                rprint(f"-> Command timeout after {timeout} seconds")
                finished = False
                returncode = -1  # Timeout error code
                stderr = f"Timeout error (limit: {timeout}s)"
                stdout = ""

                rprint(f"-> Killing children group {process.pid}")
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except ProcessLookupError:
                    rprint(
                        f"-> Failed to kill children group {process.pid}, possibly already dead"
                    )
                finally:
                    process.communicate()  # Clean up if necessary, though process should be dead.
                    rprint(f"-> Done killing children group {process.pid}")

                rprint(f"-> Remaining tries: {remaining_tries}")

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
