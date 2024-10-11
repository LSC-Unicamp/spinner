![spinner logo](assets/spinner.png){width="300"}
# Spinner

**Spinner** is an open-source, parameterized sweep benchmark tool designed for High-Performance Computing (HPC). It facilitates the efficient execution of user-supplied applications, data collection, and version control, all while using a simple YAML file format to manage configurations. Spinner is ideal for conducting repeatable, shareable, and insightful experiments across various HPC environments.

## Features

- **Parameterized Sweeps**: Dynamically replace parameters in command templates, enabling easy execution of parameter sweeps.
- **YAML Configuration**: Simplifies the setup and sharing of experimental configurations. Versioning and metadata management are built-in for reproducibility and collaboration.
- **Non-Intrusive Design**: Spinner executes user-defined commands without modifying your applications.
- **Automatic Re-run**: Automatically rerun failed experiments, making it ideal for unstable applications or testing a range of parameter combinations.
- **Data Collection**: Captures detailed output from each experiment, storing raw data and experiment metadata in dataframes. This provides a clear picture of experiment outcomes beyond summary statistics.
- **HPC Proven**: Successfully tested with major HPC applications such as LAMMPS, GROMACS, Task Bench, XSBench, and RSBench on multiple clusters.

## Getting Started

### Installation

You can install Spinner via pip:

```bash
pip install spinner
```

### Quick Start

1. **Create a YAML file** that defines your experiments and parameters. Example:

    ```yaml
    metadata:
        description: Timeout test
        version: "1.0"
        runs: 1
        timeout: 5
        retry: False
        retry_limit: 0

        sleep_test:
            command:
                template: >
                    sleep {{sleep_ammount}} && printf "
                    I slept {{sleep_ammount}}
                    # this may not print due to timeout!
                    "

    sleep_test:
        sleep_ammount:
            - 1
            - 200
    ```

2. **Run Spinner** with your configuration:

    ```bash
    spinner -c timeout_test.yaml -r -o timeout_test.pkl
    ```

3. **Collect Results**: Spinner will log the results, including runtime metrics and application output, in dataframes for easy analysis.

## Documentation

For full documentation, including advanced usage and configuration options, please visit the [official documentation](#).

## Contributing

We welcome contributions! Please check the [contribution guidelines](contribute.md) for more information.
