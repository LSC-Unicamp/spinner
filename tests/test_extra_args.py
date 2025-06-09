import pytest

from spinner.schema import SpinnerBenchmark
from spinner.cli.util import ExtraArgs


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
