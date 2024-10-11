# Spinner

<img src="spinner.png" alt="drawing" width="200"/>

## Contributting
Read the [Contribution Guidelines](docs/contribute.md).

## Setting up environment

```sh
python3 -m ensurepip
python3 -m pip3 install virtualenv
python3 -m virtualenv .venv
source .venv/bin/activate
python3 -m pip install pip --upgrade
python -m pip install .
```

## Running

Check examples in the docs folder. Check plotting examples in the notebook `spinner/exporter/reporter.ipynb`. This is the notebook that the command `--export` uses.

```sh
spinner --help
Usage: spinner [OPTIONS]

Options:
  -c, --config TEXT       Benchmark configuration file
  -r, --run               Run all benchmarks
  -e, --export            Export results to report.html
  -o, --output TEXT       Output File (.pkl)
  -ea, --extra-args TEXT  Extra arguments as key=value pairs, separated by
                          semicolons.
  --help                  Show this message and exit.
```
