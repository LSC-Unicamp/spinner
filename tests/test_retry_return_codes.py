import pandas as pd

from spinner.app import SpinnerApp
from spinner.runner.instance_runner import InstanceRunner
from spinner.schema import (
    SpinnerApplication,
    SpinnerApplications,
    SpinnerBenchmark,
    SpinnerBenchmarks,
    SpinnerCommand,
    SpinnerConfig,
    SpinnerMetadata,
)


class DummyProgress:
    def step(self):
        pass


def test_retry_on_return_code(tmp_path):
    file_path = tmp_path / "count.txt"
    cmd = f"bash -c 'echo run >> {file_path} && exit 1'"

    metadata = SpinnerMetadata(
        description="retry",
        version="1.0",
        runs=1,
        timeout=5,
        retry=2,
        retry_use_return_code=True,
        envvars=[],
    )

    applications = SpinnerApplications(
        {
            "fail": SpinnerApplication(
                command=SpinnerCommand(cmd), failed_return_codes=[1]
            )
        }
    )
    bench = SpinnerBenchmark({"dummy": [0]})
    benchmarks = SpinnerBenchmarks({"fail": bench})

    config = SpinnerConfig(
        metadata=metadata, applications=applications, benchmarks=benchmarks
    )

    df = pd.DataFrame(columns=["name", *config.applications.variables, "time"])

    runner = InstanceRunner(
        SpinnerApp.get(),
        config,
        name="fail",
        benchmark=bench,
        dataframe=df,
        progress=DummyProgress(),
    )

    runner.run_with_parameters({"dummy": 0})

    # two attempts should append two lines
    assert file_path.read_text().count("run") == 2
    # no successful rows recorded
    assert df.empty


def test_retry_on_timeout(tmp_path):
    file_path = tmp_path / "count.txt"
    cmd = f"bash -c 'echo run >> {file_path}; sleep 1'"

    metadata = SpinnerMetadata(
        description="noretry",
        version="1.0",
        runs=1,
        timeout=0.1,
        retry=2,
        retry_use_return_code=False,
        envvars=[],
    )

    applications = SpinnerApplications(
        {"fail": SpinnerApplication(command=SpinnerCommand(cmd))}
    )
    bench = SpinnerBenchmark({"dummy": [0]})
    benchmarks = SpinnerBenchmarks({"fail": bench})

    config = SpinnerConfig(
        metadata=metadata, applications=applications, benchmarks=benchmarks
    )

    df = pd.DataFrame(columns=["name", *config.applications.variables, "time"])

    runner = InstanceRunner(
        SpinnerApp.get(),
        config,
        name="fail",
        benchmark=bench,
        dataframe=df,
        progress=DummyProgress(),
    )

    runner.run_with_parameters({"dummy": 0})

    # two attempts due to timeout retry
    assert file_path.read_text().count("run") == 2


def test_successful_return_code(tmp_path):
    file_path = tmp_path / "count.txt"
    cmd = f"bash -c 'echo run >> {file_path} && exit 1'"

    metadata = SpinnerMetadata(
        description="success",
        version="1.0",
        runs=1,
        timeout=5,
        retry=0,
        retry_use_return_code=True,
        envvars=[],
    )

    applications = SpinnerApplications(
        {
            "app": SpinnerApplication(
                command=SpinnerCommand(cmd), successful_return_codes=[1]
            )
        }
    )
    bench = SpinnerBenchmark({"dummy": [0]})
    benchmarks = SpinnerBenchmarks({"app": bench})

    config = SpinnerConfig(
        metadata=metadata, applications=applications, benchmarks=benchmarks
    )

    df = pd.DataFrame(columns=["name", *config.applications.variables, "time"])

    runner = InstanceRunner(
        SpinnerApp.get(),
        config,
        name="app",
        benchmark=bench,
        dataframe=df,
        progress=DummyProgress(),
    )

    runner.run_with_parameters({"dummy": 0})

    assert file_path.read_text().count("run") == 1
    assert len(df) == 1


def test_ignore_return_code(tmp_path):
    file_path = tmp_path / "count.txt"
    cmd = f"bash -c 'echo run >> {file_path} && exit 1'"

    metadata = SpinnerMetadata(
        description="ignore",
        version="1.0",
        runs=1,
        timeout=5,
        retry=1,
        retry_use_return_code=False,
        envvars=[],
    )

    applications = SpinnerApplications(
        {"app": SpinnerApplication(command=SpinnerCommand(cmd))}
    )
    bench = SpinnerBenchmark({"dummy": [0]})
    benchmarks = SpinnerBenchmarks({"app": bench})

    config = SpinnerConfig(
        metadata=metadata, applications=applications, benchmarks=benchmarks
    )

    df = pd.DataFrame(columns=["name", *config.applications.variables, "time"])

    runner = InstanceRunner(
        SpinnerApp.get(),
        config,
        name="app",
        benchmark=bench,
        dataframe=df,
        progress=DummyProgress(),
    )

    runner.run_with_parameters({"dummy": 0})

    # only one attempt despite retry=1 because return codes are ignored
    assert file_path.read_text().count("run") == 1
    assert len(df) == 1
