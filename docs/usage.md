# Usage

Spinner ships with exactly **two** commands—no more, no less.

* **`spinner run`** takes a YAML configuration, explodes the parameter matrix, executes every job, and serializes the results to a Pickle.  
* **`spinner export`** ingests that Pickle, turns the dataframe into publication‑ready PDFs, and drops a ready‑to‑hack Python notebook that already knows how to re‑parse and plot the data.

If you master these two verbs, you’ve mastered Spinner. Details follow.

---

## Spinner Run

### Command & Usage

```bash
spinner run path/to/benchmark.yaml -o output.pkl
```

That’s it—no hidden flags.  
`-o / --output` names the Pickle you’ll feed to **spinner export**.

---

### YAML Anatomy (three mandatory blocks)

We sill use the `sleep_bench` example from the examples page to illustrate the YAML structure. The full example is also available in the examples page. This benchmark has the following format:

```yaml
metadata:
# ... Metadata of the experiment

# The applications block
applications:
  sleep_bench: #  name of the application
    command:
    # Shell command to run the application

    capture:
    # ... User defined function to parse application output

    plot:
    # ... The plot block

# The substitution block
benchmarks:
  sleep_bench:
    # values to substitute : list
```

| Block | Governs | Key fields |
|-------|---------|------------|
| **`metadata`** | Global run policy | `description`, `version`, `runs`, `timeout`, `retry`, `envvars` |
| **`applications`** | How to run each binary/script **and** how to scrape its output | `command`, `capture`, `plot` |
| **`benchmarks`** | Parameter sweep matrix | `<application_name>: <param_list>` |

#### metadata

* `description` – free‑text tag for the run.  
* `runs` – how many times Spinner repeats **each** benchmark point.  
* `timeout` – wall‑clock in seconds.  
* `retry` – `false` or an integer count of auto‑retries.  
* `envvars` – list of variables to copy into the subprocess (`["PATH", "OMP_*", "*"]` allowed; globbing works).  

All of this is stored inside the Pickle so you can audit or reproduce the run later.

#### applications

The `applications` block describes how to run each benchmark. Each key is an application with an execution command, a capture spec, and a plot spec.

##### command

The `command` field is a shell command to run the application. It can be a single command or a multi-line string. The command is executed in a subprocess, and the output is captured for parsing.

The command can take `{{placeholders}}` for parameters defined in the `benchmarks` block. These placeholders are replaced with the corresponding values from the benchmark row during execution. The command can also include Jinja2-style substitutions, which allow for more complex expressions and calculations.

The user can also pass extra arguments to the command using the `--extra-args` flag. These extra arguments are passed as a dictionary to the command and can be used in the command string.

```yaml
applications:
  sleep_bench:
    command: >
      sleep {{sleep_ammount + (extra_time | int)}}
```

##### capture

The `capture` section defines how Spinner parses the output of a benchmarked application. For each line of output (stdout and optionally stderr), Spinner attempts to match the specified `pattern`. If a line matches, and a `lambda` is defined, it applies that lambda function to transform the matched string into a value. This result is stored in the resulting dataframe under the column named by `name`. Each application run contributes one row to the dataframe. A special capture type `all` can be used to store the full, unprocessed output of each execution, useful for debugging or ad-hoc parsing later.

```yaml
capture:
  - type: matches
    name: real_time
    pattern: "real"
    lambda: >
      lambda x:  (
      float(x.split("m")[0].split("\t")[1]) * 60
      +
      float(x.split("m")[1].split("s")[0])
      )
```

##### plot

The `plot` section provides a minimal configuration to generate quick visualizations of the collected results. Each entry defines a plot with `x_axis` and `y_axis`, which must reference existing columns in the dataframe. Optionally, a `group_by` field allows aggregation (via mean) across runs with the same value for that key, useful for summarizing repeated experiments. These plots serve as a quick-look feature, and the real customization is intended to happen later in the exported Jupyter notebook, where users can modify and extend the visualization logic freely.

```yaml
plot:
  - title: Real Time vs Sleep arg
    x_axis: amount
    y_axis: real_time
    group_by: amount
```

Spinner only takes one `command` per application., but you can add multiple `capture` and `plot` specs.

**`benchmarks` block—define substitution values**

```yaml
benchmarks:
  sleep_bench:
    sleep_ammount:
      - 1
      - 2
```

Spinner builds the Cartesian product of every parameter list. Two params with three values each will produce six runs.

---

### Resulting DataFrame

| name        | amount | real_time | time      |
|-------------|-------:|----------:|----------:|
| sleep_bench | 1      | 1.001     | 1.017826 |
| sleep_bench | 1      | 1.001     | 1.018214 |
| sleep_bench | 1      | 1.002     | 1.018200 |
| sleep_bench | 1      | 1.001     | 1.018286 |
| sleep_bench | 1      | 1.001     | 1.017482 |
| sleep_bench | 2      | 2.001     | 2.017277 |
| sleep_bench | 2      | 2.001     | 2.017766 |
| sleep_bench | 2      | 2.001     | 2.015588 |
| sleep_bench | 2      | 2.001     | 2.017538 |
| sleep_bench | 2      | 2.002     | 2.015914 |

* **`name`** – which `applications` entry ran (`sleep_bench`).  
* **`amount`** – value injected into `{{amount}}`.  
* **`real_time`** – parsed by the `capture` lambda:  

  ```python
  lambda x: (
      float(x.split("m")[0].split("\t")[1]) * 60 +
      float(x.split("m")[1].split("s")[0])
  )
  ```  

* **`time`** – end‑to‑end wall time Spinner measures automatically.

---

## Spinner Export

```bash
spinner export -i output.pkl
```

Pipeline:

1. **Load** the Pickle (dataframe + YAML config).  
2. **Clean** NaNs/duplicates and enforce numeric dtypes.  
3. **Bootstrap** 95 % confidence intervals when `runs ≥ 2`.  
4. **Plot** error‑bar PDFs per each `plot` spec.  
5. **Dump** everything into `./output-<bench-name>/`.  
6. **Add** an `<bench-name>.ipynb` notebook with the kick‑start analysis code—extend it as you see fit.

Need seaborn grids, mixed‑effects models, or database ingestion? Crack open the notebook and go wild; Spinner’s promise ends once you have clean data, baseline plots, and reproducibility baked in.
