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
