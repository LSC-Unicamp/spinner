import subprocess
from runner.instance_runner import InstanceRunner
from rich import print as rprint
import os


class MPIRunner(InstanceRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_run_instruction(self):
        instructions = []
        for nodes in self.sweep_parameters["nodes"]:
            for procs in self.sweep_parameters["procs"]:
                for read_step in self.sweep_parameters["read_step"]:
                    ppn = procs // nodes
                    input_file = self.metadata["input_file"]
                    input_file = os.path.abspath(input_file)
                    bin_path = "./benchs/mpi-io/build/mpi_io_count"
                    bin_path = os.path.abspath(bin_path)
                    assert os.path.exists(
                        bin_path
                    ), f"Binary path {bin_path} does not exist"

                    if self.metadata["hosts"] is None:
                        rprint("[red]Warning: No hosts provided, running MPI locally")
                        host_num = 1
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

                    if ppn == 0:
                        rprint(
                            f"[yellow]Skipping procs={procs}, nodes={nodes} since ppn=0"
                        )
                        continue
                    if nodes > host_num:
                        rprint(
                            f"Skipping procs={procs}, nodes={nodes} since nodes > {host_num} hosts"
                        )
                        continue

                    # TODO add option to call srun
                    cmd = f"mpirun -np {procs} -ppn {ppn} {bin_path} {input_file} {read_step}"
                    if self.metadata["hosts"] is not None:
                        cmd = f"mpirun -np {procs} -ppn {ppn} -hosts {','.join(host_list)} {bin_path} {input_file} {read_step}"
                    instructions.append(
                        {
                            "cmd": cmd,
                            "parameters": {
                                "procs": procs,
                                "nodes": nodes,
                                "read_step": read_step,
                            },
                        }
                    )
        return instructions
