from runner.instance_runner import InstanceRunner


class MPIRunner(InstanceRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def run(self, timeout, progress_callback=None):
        pass
