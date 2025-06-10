import pickle

from spinner.app import SpinnerApp
from spinner.runner import run
from spinner.schema import SpinnerConfig


def test_capture_all_basic(tmp_path):
    config = SpinnerConfig.from_data(
        {
            "metadata": {
                "description": "capture all",
                "version": "1.0",
                "runs": 1,
                "timeout": 5,
                "retry": 0,
                "envvars": [],
            },
            "applications": {
                "echo": {
                    "command": "echo hello",
                    "capture": [
                        {
                            "type": "all",
                            "name": "raw_output",
                        }
                    ],
                }
            },
            "benchmarks": {"echo": {}},
        }
    )

    output = tmp_path / "out.pkl"
    run(SpinnerApp.get(), config, output.open("wb"))

    data = pickle.loads(output.read_bytes())
    df = data["dataframe"]
    assert df["raw_output"].iloc[0].strip() == "hello"

