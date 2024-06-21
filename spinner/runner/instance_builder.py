import os
import shutil
import subprocess
from rich import print as rprint
import json


def build_all(config):
    config = json.load(open(config))
    bench_names = [bench_name for bench_name in config if bench_name != "metadata"]

    # TODO: move this somewhere else
    bench_builder = {
        "mpi-io": InstanceBuilder,
        "omp-tasks": InstanceBuilder,
    }

    for bench in bench_names:
        meta_info = config["metadata"][bench]["build"]
        builder = bench_builder[bench](meta_info)

        builder.build()

        rprint(meta_info)

    exit(0)


class InstanceBuilder:
    def __init__(self, meta_info):
        self.meta_info = meta_info

    def build(self):
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

        env = self.meta_info["env"]
        cmake_flags = self.meta_info["cmake_flags"]
        make_flags = self.meta_info["make_flags"]

        # run cmake
        cmake_cmd = ["cmake", ".."]
        subprocess.run(cmake_cmd + cmake_flags, env=env)

        # run make
        make_cmd = ["make"]
        subprocess.run(make_cmd + make_flags, env=env)

        # move back to original directory
        os.chdir(orig_dir)

        raise NotImplementedError
