from runner.instance_runner import InstanceRunner
import os
from rich import print as rprint
from jinja2 import Template, Environment, Undefined


class StrictUndefined(Undefined):
    def __getattr__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __getitem__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __str__(self):
        raise NameError(f"'{self._undefined_name}' is undefined")


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
                rprint(f"self.metadata: {self.metadata}")
                command_info = self.metadata["omp-tasks"]["command"]
                template_string = command_info["template"]
                rprint(f"command_template: {template_string}")
                input_file = os.path.abspath(input_file)

                # bin_path = "./benchs/omp-tasks/build/lustre1"
                # bin_path = os.path.abspath(bin_path)
                # assert os.path.exists(
                #     bin_path
                # ), f"Binary path {bin_path} does not exist"

                env = Environment(undefined=StrictUndefined)
                template = env.from_string(template_string)

                base_path = self.metadata["omp-tasks"]["build"]["path"]

                command = template.render(
                    input_file=input_file,
                    tasks=n_tasks,  # TODO: rename for consistency
                    read_step=read_step,
                    base_path=base_path,
                )
                rprint(f"rendered command: {command}")

                # cmd = f"{bin_path} -f {input_file} -t {n_tasks} -r {read_step}"
                instructions.append(
                    {
                        "cmd": command,
                        "parameters": {
                            "tasks": n_tasks,
                            "read_step": read_step,
                        },
                    }
                )
        return instructions
