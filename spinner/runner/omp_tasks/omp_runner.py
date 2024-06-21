from runner.instance_runner import InstanceRunner
import os


class OmpRunner(InstanceRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_bench_name(self):
        return "omp-tasks"

    def get_run_instruction(self):
        instructions = []
        for n_tasks in self.config["tasks"]:
            for read_step in self.config["read_step"]:
                input_file = self.metadata["input_file"]
                input_file = os.path.abspath(input_file)
                bin_path = "./benchs/omp-tasks/build/lustre1"
                bin_path = os.path.abspath(bin_path)
                assert os.path.exists(
                    bin_path
                ), f"Binary path {bin_path} does not exist"

                cmd = f"{bin_path} -f {input_file} -t {n_tasks} -r {read_step}"
                instructions.append(
                    {
                        "cmd": cmd,
                        "parameters": {
                            "tasks": n_tasks,
                            "read_step": read_step,
                        },
                    }
                )
        return instructions
