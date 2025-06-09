# Examples

Below are various examples demonstrating Spinner’s capabilities. Each example includes a YAML snippet (embedded with the [mkdocs-include plugin](https://github.com/mondeja/mkdocs-include-markdown-plugin)) so you can run them directly or adapt them to your needs.

## 1. Simple Sleep Benchmark

A minimal illustration of how Spinner handles a small parameter sweep. Runs two different `sleep_amount` values:

```yaml
--8<-- "./docs/examples/sleep_benchmark.yaml"
```

**How to run**:

```bash
spinner run docs/examples/sleep_benchmark.yaml -o output.pkl
```

This will produce a `sleep_results.pkl` file containing run metadata and any captured output.

## 2. Capturing Command Output

Demonstrates capturing and parsing output (in this case, timing info from the `time` command). Useful for HPC applications that print performance metrics on stdout.

```yaml
--8<-- "./docs/examples/capture_output.yaml"
```

**How to run**:

```bash
spinner run docs/examples/capture_output.yaml
```

Check the resulting dataframe for the extracted timing fields (`real_time`).

## 3. Passing Extra Arguments (`--extra-args`)

Shows how to pass extra parameters at runtime without editing the YAML. This is helpful when HPC scripts need certain parameters (like `hosts`) populated by the scheduler or environment.

```yaml
--8<-- "./docs/examples/extra_args.yaml"
```

**How to run**:

```bash
spinner run docs/examples/extra_args.yaml --extra-args "extra_time=4"
```

Here, `extra_time=2` is added on top of `sleep_ammount`.

## 4. Extra Args with Comma Values

Demonstrates passing a value that contains commas without it being split
into a list. The command simply echoes the provided hosts string.

```yaml
--8<-- "./docs/examples/extra_args_list.yaml"
```

**How to run**:

```bash
spinner run docs/examples/extra_args_list.yaml --extra-args "hosts=machineA,machineB"
```

The `hosts` value remains a single string and is not expanded into a list.

## 5. Extra Args with List Values

Demonstrates passing a list of values to be swept using the `--extra-args`
flag. Each value will result in a separate run.

```yaml
--8<-- "./docs/examples/extra_args_sleep_list.yaml"
```

**How to run**:

```bash
spinner run docs/examples/extra_args_sleep_list.yaml --extra-args 'sleep_time=[1,2]'
```

## 6. Timeout Handling

Demonstrates automatic timeout behavior. If a command exceeds the specified timeout, Spinner stops it and records a failure (optionally rerunning if `retry` is enabled).

```yaml
--8<-- "./docs/examples/timeout_test.yaml"
```

**How to run**:

```bash
spinner run docs/examples/timeout_test.yaml
```

Spinner will attempt to run both `sleep_amount` values; the 200-second sleep will hit the 5-second timeout.

## 5. Zipping Parameters

Sometimes you want two parameters to vary together rather than producing all
possible combinations. Add a `zip` key under your benchmark to pair parameter
lists element-wise.

```yaml
--8<-- "./docs/examples/zip_pairs.yaml"
```

This example runs `ompc_baseline.sif` with `tb_baseline/main` and
`ompc_better_sched.sif` with `tb_better_sched/main`.

---

**Tip**: Use the `plot` directives in your YAML configs to automatically generate charts from the collected data. For more details, see the `capture_output.yaml` example’s `plot` section.

Return to the [Main Page](index.md) or learn about [Using Spinner with SLURM](slurm.md).
