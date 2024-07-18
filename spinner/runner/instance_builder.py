import os
import shutil
import subprocess
from rich import print as rprint
from rich.progress import Progress
import json
from jinja2 import Template, Environment, Undefined


# TODO: move this to an utility function
class StrictUndefined(Undefined):
    def __getattr__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __getitem__(self, name):
        raise NameError(f"'{name}' is undefined")

    def __str__(self):
        raise NameError(f"'{self._undefined_name}' is undefined")


def build_all(config):
    config = json.load(open(config))
    bench_names = [bench_name for bench_name in config if bench_name != "metadata"]

    # TODO: move this somewhere else
    bench_builder = {
        "mpi-io": InstanceBuilder,
        "omp-tasks": InstanceBuilder,
    }

    with Progress() as progress:
        task = progress.add_task("Building benchmarks", total=len(bench_names))
        for bench in bench_names:
            meta_info = config["metadata"][bench]
            builder = bench_builder[bench](meta_info)

            builder.build()
            progress.update(task, advance=1)


class InstanceBuilder:
    def __init__(self, meta_info):
        self.meta_info = meta_info

    def build(self) -> None:
        rprint(f"Building in path {self.meta_info['bench_path']}")
        rprint(self.meta_info)
        # get current directory
        orig_dir = os.getcwd()

        # move to bench directory
        assert os.path.exists(
            self.meta_info["bench_path"]
        ), f"Path {self.meta_info['bench_path']} does not exist"

        # save original environment variables
        original_vars = os.environ.copy()

        # set environment variables
        env_vars = os.environ.copy()
        env_vars.update(self.meta_info["env"])

        env = Environment(undefined=StrictUndefined)
        for build_instruction in self.meta_info["build_instructions"]:
            rprint(f"Building {build_instruction}")
            cmd = env.from_string(build_instruction["command"]).render(self.meta_info)
            cwd = env.from_string(build_instruction["cwd"]).render(self.meta_info)
            rprint(f"Running command: {cmd} in {cwd}")

            result = subprocess.run(
                cmd,
                cwd=cwd,
                env=env_vars,
                check=True,
                shell=True,
                capture_output=True,
                text=True,
            )
            rprint(result.stdout)
            rprint(result.stderr)

        # restore original environment variables
        os.environ = original_vars

        # move back to original directory
        os.chdir(orig_dir)
