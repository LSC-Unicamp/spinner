import pickle
from pathlib import Path

import pytest
import yaml

from spinner.app import SpinnerApp
from spinner.cli.util import ExtraArgs
from spinner.runner import run
from spinner.schema import SpinnerBenchmark, SpinnerConfig


def test_extra_args_parser():
    parser = ExtraArgs()
    result = parser.convert("hosts=machineA,machineB", None, None)
    assert result == {"hosts": "machineA,machineB"}


def test_extra_args_parser_list():
    parser = ExtraArgs()
    result = parser.convert("sleep_time=[1,2]", None, None)
    assert result == {"sleep_time": [1, 2]}


def test_sweep_parameters_with_string_extra():
    bench = SpinnerBenchmark({"node_count": [1, 2]})
    params = bench.sweep_parameters({"hosts": "machineA,machineB"})
    assert params == [
        {"node_count": 1, "hosts": "machineA,machineB"},
        {"node_count": 2, "hosts": "machineA,machineB"},
    ]


def test_sweep_parameters_with_list():
    bench = SpinnerBenchmark({"sleep_amount": [1, 2]})
    params = bench.sweep_parameters({"extra_time": [3, 4]})
    assert params == [
        {"sleep_amount": 1, "extra_time": 3},
        {"sleep_amount": 1, "extra_time": 4},
        {"sleep_amount": 2, "extra_time": 3},
        {"sleep_amount": 2, "extra_time": 4},
    ]


def test_run_example_extra_args(tmp_path):
    path = Path("docs/examples/extra_args_list.yaml")
    config = SpinnerConfig.from_data(yaml.safe_load(path.read_text()))
    output = tmp_path / "out.pkl"

    run(SpinnerApp.get(), config, output.open("wb"), hosts="machineA,machineB")

    data = pickle.loads(output.read_bytes())
    df = data["dataframe"]
    assert df["hosts"].iloc[0] == "machineA,machineB"


def test_run_example_extra_args_list(tmp_path):
    path = Path("docs/examples/extra_args_sleep_list.yaml")
    config = SpinnerConfig.from_data(yaml.safe_load(path.read_text()))
    output = tmp_path / "out.pkl"

    run(SpinnerApp.get(), config, output.open("wb"), sleep_time=[1, 2])

    data = pickle.loads(output.read_bytes())
    df = data["dataframe"]
    assert df["sleep_time"].tolist() == [1, 2]


def test_run_benchmark_with_multiple_applications(tmp_path):
    config = SpinnerConfig.from_data(
        {
            "metadata": {"description": "x", "version": "1.0", "runs": 1},
            "applications": {
                "a1": {"command": "echo run"},
                "a2": {"command": "echo run"},
            },
            "benchmarks": {
                "grouped": {
                    "app": ["a1", "a2"],
                    "value": [1],
                }
            },
        }
    )
    output = tmp_path / "out.pkl"
    run(SpinnerApp.get(), config, output.open("wb"))
    data = pickle.loads(output.read_bytes())
    assert sorted(data["dataframe"]["name"].tolist()) == ["a1", "a2"]


def test_run_single_benchmark_with_benchmark_flag(tmp_path):
    config = SpinnerConfig.from_data(
        {
            "metadata": {"description": "x", "version": "1.0", "runs": 1},
            "applications": {
                "a1": {"command": "echo run"},
                "a2": {"command": "echo run"},
            },
            "benchmarks": {
                "bench_1": {"app": ["a1"], "value": [1]},
                "bench_2": {"app": ["a2"], "value": [2]},
            },
        }
    )
    output = tmp_path / "out.pkl"
    run(SpinnerApp.get(), config, output.open("wb"), benchmark="bench_1")
    data = pickle.loads(output.read_bytes())
    assert data["dataframe"]["name"].tolist() == ["a1"]
