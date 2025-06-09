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
    result = parser.convert("hosts=sorgan-cpu1,sorgan-cpu2", None, None)
    assert result == {"hosts": "sorgan-cpu1,sorgan-cpu2"}


def test_sweep_parameters_with_string_extra():
    bench = SpinnerBenchmark({"node_count": [1, 2]})
    params = bench.sweep_parameters({"hosts": "sorgan-cpu1,sorgan-cpu2"})
    assert params == [
        {"node_count": 1, "hosts": "sorgan-cpu1,sorgan-cpu2"},
        {"node_count": 2, "hosts": "sorgan-cpu1,sorgan-cpu2"},
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

    run(SpinnerApp.get(), config, output.open("wb"), hosts="sorgan-cpu1,sorgan-cpu2")

    data = pickle.loads(output.read_bytes())
    df = data["dataframe"]
    assert df["hosts"].iloc[0] == "sorgan-cpu1,sorgan-cpu2"
