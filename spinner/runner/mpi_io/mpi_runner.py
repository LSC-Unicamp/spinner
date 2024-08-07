import itertools
import subprocess

from rich import print as rprint
from runner.instance_runner import InstanceRunner


class MPIRunner(InstanceRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_parameter_combinations(self):
        parameter_combinations = super().get_parameter_combinations()

        tailored_parameters = []

        for parameter in parameter_combinations:
            if self.metadata["hosts"] is None:
                rprint("[red]Warning: No hosts provided, running MPI locally")
                host_num = 1
                host_list = "localhost"
            else:
                host_list = self.metadata["hosts"]
                # expand list using scontrol show hostname "sdumont[xxxx]"
                host_list = subprocess.run(
                    ["scontrol", "show", "hostname", host_list],
                    capture_output=True,
                    text=True,
                ).stdout
                host_list = host_list.split()

                host_num = len(host_list)
                rprint(f"Got hosts {host_num}: {host_list}")

            parameter["hosts"] = host_list
            parameter["ppn"] = 1
            rprint(f"Parameter: {parameter}")
            tailored_parameters.append(parameter)

        return tailored_parameters
