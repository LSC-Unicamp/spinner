import textwrap
from pathlib import Path

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

import spinner
from spinner.app import SpinnerApp


def run_reporter(notebook_path, pkl_db_path=None):
    # Resolve folder and base name (remove .pkl extension)
    # Resolve folder and base name (remove .pkl extension)
    pkl_db_path = Path(pkl_db_path)
    pkl_db_folder = pkl_db_path.parent
    base_name = pkl_db_path.stem  # Remove the extension

    # Paths for the new .ipynb and .html
    new_notebook_path = pkl_db_folder / f"{base_name}.ipynb"
    new_html_path = pkl_db_folder / f"{base_name}.html"

    # Read the input notebook
    with open(notebook_path, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # Modify the parameters in the first code cell
    param_cell_index = 0  # First cell hold parameters
    nb.cells[param_cell_index].source = textwrap.dedent(
        f"""
    # Default locations if parameter not passed
    benchmark_data_path = "{pkl_db_path}"
    output_folder = "{pkl_db_folder}/output-{base_name}"
    """
    )

    # Set up the notebook execution configuration
    try:
        execute_preprocessor = ExecutePreprocessor(timeout=600, kernel_name="python3")
        execute_preprocessor.preprocess(nb, {"metadata": {"path": pkl_db_folder}})
    except Exception as e:
        SpinnerApp.print(f"[b red]ERROR[/]: Error executing the notebook: {e}")
    finally:
        # Write the executed notebook to disk in the user folder
        with open(new_notebook_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)

    # Export the executed notebook to HTML
    html_exporter = HTMLExporter()
    html_exporter.template_name = "classic"
    (html_body, resources) = html_exporter.from_notebook_node(nb)

    # Write the HTML output
    with open(new_html_path, "w", encoding="utf-8") as f:
        f.write(html_body)
