# Future

This contains our view of the Spinner application, when ready.

## Possible usages

```sh
spinner --use-slurm sorgan.json --group-jobs-by nodes,repetition -c benchmark.json -r T
```

This will launch one separeted Slurm job per input configuration, but inputs that are repetition (for each nrun) and inputs with specific number of nodes will be aggregated on the same slurm job.

```sh
spinner --use-slurm sorgan.json --group-jobs-by nodes,repetition -c benchmark.json -r T --dry-run --assert-environmnet
```

This will assert that the enrivonment is corret: LD_LIBRARY_PATH, if binaries are there, if we have the permissions on the partitions. There is a fixed list, common to all benchmarks, and a list that inherited classes can provide, additionaly. The dry-run flag make it so nothing is actually ran, only reported.


## Features

- Asserts
  - Benchmark-wise: check if commads are feasible before start (i.e. check for libraries and build binaries)
  - System-wise: check if current number of nodes are avaliable

- Runner
  - Collect metrics and save to dataframe
  - Track progress
  - Automatically launch Slurm, or mpirun directly if run from allocation (e.g. check for env vars in slurm envinroments)

- Resiliency
  - Keep going of excepetion happens at one execution (and notify user)
  - Save status after each run to PKL file

- Profile
  - Automatic plot of total time
  - Automatic instrumentation stacked plot (using JSON expression match)
  - Metadata tracker: instrument enviroment and save to PKL with each dataframe of all executions
  - Statistics: use best-practices for confidence interval (not using mean, not using std dev - use Bootstrap intead)


## Configurations (JSON)

Cluster config: account, partitions and limits. Templates for launching applications: `srun`, or `mpirun` (or neither). They should prefix the application binary if the application specifies a launcher in their JSON.

Application config: sweep parameters, their usage in the invocation (template, JINJA for example). Profiling and instrumentation: if on, a REGEXP on how to grep the output of the application to plot stacked bars.

Example:

### Application Configuration JSON

```json
{
    "metadata": {
        "description": "I/O benchmarks",
        "version": "1.0",
        "runs": 30,
        "timeout": 600,
        "input_file": "random_numbers.bin",
        "command_template": "srun --nodes={{ nodes }} --ntasks={{ tasks }} --time={{ timeout }} {{ executable }}",
        "use_allocated_node": false,
        "cluster_config": "cluster_config.json",
        "profiling": {
            "enabled": true,
            "patterns": {
                "execution_time": "Execution time: (\\d+\\.\\d+) seconds",
                "memory_usage": "Memory usage: (\\d+\\.\\d+) MB"
            }
        },
        "omp-tasks": {
            "build": {
                "cmake_flags": ["-DCMAKE_BUILD_TYPE=Release"],
                "make_flags": ["-j"],
                "env": {"CC": "gcc", "CXX": "g++"},
                "path": "benchs/omp-tasks"
            }
        },
        "mpi-io": {
            "build": {
                "cmake_flags": ["-DCMAKE_BUILD_TYPE=Release"],
                "make_flags": ["-j"],
                "env": {"CC": "mpicc", "CXX": "mpicxx"},
                "path": "benchs/mpi-io"
            }
        }
    },
    "omp-tasks": {
        "tasks": [1, 2, 32, 64],
        "read_step": [100, 100000, 1000000]
    },
    "mpi-io": {
        "nodes": [1, 2],
        "procs": [1, 8, 32],
        "read_step": [100, 100000, 1000000]
    }
}
```

### Cluster Configuration JSON

```json
{
    "srun_account": "default_account",
    "partition": "default_partition",
    "time_limit": "01:00:00"
}
```

## CLI

Command line options:

- `--config`, `-c`: Path to the benchmark configuration file. Default is `bench_settings.json`.
- `--build`, `-b`: Boolean flag to build all benchmarks. Default is `False`.
- `--output`, `-o`: Path to the output file.
- `--run`, `-r`: Boolean flag to run all benchmarks. Default is `False`.
- `--export`, `-e`: Boolean flag to export results to `report.html`. Default is `True`.
- `--hosts`, `-h`: Comma-separated list of hosts.
- `--dry-run`, `-d`: Boolean flag to perform a dry run without executing the commands. Default is `False`.

## Modules architecture and signatures

### Modules

1. **runner/config_loader.py**
   - Load and validate configuration files.

2. **runner/command_executor.py**
   - Execute commands and handle dry runs.

3. **runner/profiler.py**
   - Parse profiling information from command output.

4. **runner/benchmark_builder.py**
   - Build benchmarks.

5. **runner/benchmark_runner.py**
   - Run benchmarks and handle results.

### Function Signatures

#### config_loader.py

```python
def load_config(config_path: str) -> dict:
    """Load and validate the configuration file."""
```

#### command_executor.py

```python
def execute_command(template: str, context: dict, dry_run: bool) -> tuple:
    """Execute a command using a Jinja template and context."""
```

#### profiler.py

```python
def parse_profiling_info(output: str, patterns: dict) -> dict:
    """Parse profiling information from command output using regex patterns."""
```

#### benchmark_builder.py

```python
def build_all(config: dict):
    """Build all benchmarks as specified in the configuration."""
```

#### benchmark_runner.py

```python
def run_benchmarks(config: dict, hosts: str):
    """Run all benchmarks as specified in the configuration."""
```