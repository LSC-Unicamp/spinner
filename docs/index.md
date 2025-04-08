![spinner logo](assets/spinner.png){width="300"}

# Spinner

**Spinner** is an open-source, parameterized sweep benchmark tool for High-Performance Computing (HPC). It runs user-supplied commands with varying parameters, collecting output and recording metadata in a straightforward, YAML-based configuration.

## Key Features

- **Parameterized Sweeps**: Define arbitrary parameter sweeps in YAML.
- **Non-Intrusive**: Runs your existing scripts or applications unchanged.
- **Re-run and Timeout Handling**: Automatically retry failed runs and enforce timeouts.
- **Automatic Data Collection**: Captures logs, metrics, and metadata into concise dataframes.
- **YAML Configuration**: Reproducible, shareable configs for HPC workloads.

## Quick Start

1. **Install Spinner**:

   ```bash
   pip install spinner
   ```

2. **Create a YAML file** defining parameters and commands. For a minimal example:

   ```yaml
   --8<-- "./docs/examples/sleep_benchmark.yaml"
   ```

3. **Run Spinner**:

   ```bash
   spinner -c sleep_benchmark.yaml -r -o results.pkl
   ```

   This runs all parameter combinations, retries failures (if configured), and stores the results in `results.pkl`.

## Documentation & Examples

- **Examples**: See [Examples](examples.md) for a gallery of ready-to-run YAML files showcasing parameter sweeps, capturing output from commands, handling timeouts, and more.
- **SLURM HPC**: Refer to [Using with SLURM](slurm.md) for tips on incorporating Spinner in batch jobs.
- **Contributing**: Check out [Contribute to Spinner](contribute.md) for development guidelines, linting policy, and release automation steps.

## Citation

If you use Spinner in your research, please cite it.

```bibtex
--8<-- "./docs/assets/citation.bib"
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
