from runner.instance_runner import InstanceRunner


class OmpRunner(InstanceRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_bench_name(self):
        return "omp-tasks"
