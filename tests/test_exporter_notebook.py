import json
from pathlib import Path


def test_reporter_skips_benchmarks_without_plot_configuration():
    notebook = json.loads(Path("spinner/exporter/reporter.ipynb").read_text())
    code_cells = [
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]

    guard = "if not bench_plots:\n        print(f\"Skipping {bench}: no plot configuration found.\")\n        continue"

    assert sum(guard in cell for cell in code_cells) == 2
