# Spinner

<img src="spinner.png" alt="drawing" width="200"/>

## Overview

**Spinner** is an open-source, parameterized sweep benchmark tool for High-Performance Computing (HPC). It executes user-defined applications across multiple parameter combinations, automatically collects output, and maintains version-controlled experiment configurations. Thanks to its simple YAML format, Spinner helps you run repeatable and shareable experiments in various HPC environments.

## Usage

For **examples**, **installation instructions**, and a quick start guide, visit the [Spinner Documentation](https://lsc-unicamp.github.io/spinner/).

Spinner is distributed as a Python package and can be installed via `pip`:

```bash
pip install spinner
```

To enable the optional export features that rely on Jupyter, install with:

```bash
pip install 'spinner[exporter]'
```

## Logging & Verbosity

Use `-v` or `-vv` with any command to increase logging output. `-v` prints each
rendered command and retry notice. `-vv` additionally prints the command output
and return codes. When a verbosity flag is used, the logger level is set to
`INFO`; otherwise it falls back to the `LOGLEVEL` environment variable (default
`WARNING`). Set `LOGLEVEL=DEBUG` to see developer messages.

## Contributing

To learn how to set up your development environment and contribute to Spinner, please refer to the [Contribution Guidelines](docs/contribute.md).

## Citation

If you use Spinner in your research, kindly cite it. Citation details are provided in the [documentation](https://lsc-unicamp.github.io/spinner#citation).
