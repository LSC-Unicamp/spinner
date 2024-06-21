from runner.instance_runner import InstanceRunner
import os


class MPIRunner(InstanceRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_bench_name(self):
        return "mpi-io"

    def get_run_instruction(self):
        instructions = []
        for n_nodes in self.config["nodes"]:
            for n_procs in self.config["procs"]:
                for read_step in self.config["read_step"]:
                    ppn = n_procs // n_nodes
                    if ppn == 0:
                        # rprint(f"Skipping n_procs={n_procs}, n_nodes={n_nodes} since ppn=0")
                        continue
                    input_file = self.metadata["input_file"]
                    input_file = os.path.abspath(input_file)
                    bin_path = "./benchs/mpi-io/build/mpi_io_count"
                    bin_path = os.path.abspath(bin_path)
                    assert os.path.exists(
                        bin_path
                    ), f"Binary path {bin_path} does not exist"

                    cmd = f"mpirun -np {n_procs} -ppn {ppn} {bin_path} {input_file} {read_step}"
                    instructions.append(
                        {
                            "cmd": cmd,
                            "parameters": {
                                "n_procs": n_procs,
                                "n_nodes": n_nodes,
                                "read_step": read_step,
                            },
                        }
                    )
        return instructions
