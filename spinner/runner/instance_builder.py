import os
import shutil
import subprocess
from rich import print as rprint
from rich.progress import Progress
import json


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
        rprint(f"Building in path {self.meta_info['path']}")
        rprint(self.meta_info)
        # get current directory
        orig_dir = os.getcwd()

        # move to bench directory
        os.chdir(self.meta_info["path"])

        # delete 'build' folder, if exists
        build_dir = os.path.join(os.getcwd(), "build")

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        os.makedirs(build_dir)

        os.chdir(build_dir)

        original_vars = os.environ.copy()
        env_vars = os.environ.copy()
        env_vars.update(self.meta_info["env"])
        cmake_flags = self.meta_info["build"]["cmake_flags"]
        make_flags = self.meta_info["build"]["make_flags"]

        cmake_command = ["cmake", ".."] + cmake_flags
        make_command = ["make"] + make_flags

        result = subprocess.run(
            cmake_command, env=env_vars, check=True, capture_output=True, text=True
        )
        rprint(result.stdout)
        rprint(result.stderr)

        result = subprocess.run(
            make_command, env=env_vars, check=True, capture_output=True, text=True
        )
        rprint(result.stdout)
        rprint(result.stderr)

        # restore original environment variables
        os.environ = original_vars

        # move back to original directory
        os.chdir(orig_dir)
