import os

import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor


def run_reporter(notebook_path, output_path, pkl_db_path=None):
    with open(notebook_path, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # Modify the parameters in the first code cell
    pkl_db_folder = os.path.dirname(pkl_db_path)
    param_cell_index = 0  # First cell hold parameters
    nb.cells[
        param_cell_index
    ].source = f"""
    # Default locations if parameter not passed
    benchmark_data_path = "{pkl_db_path}"
    output_folder = "{pkl_db_folder}/output"
    """

    # Set up the notebook execution configuration
    execute_preprocessor = ExecutePreprocessor(timeout=600, kernel_name="python3")

    # Execute the notebook
    execute_preprocessor.preprocess(nb, {"metadata": {"path": pkl_db_folder}})

    # Set up the HTML exporter
    html_exporter = HTMLExporter()
    html_exporter.template_name = "classic"

    # Convert notebook to HTML
    (html_body, resources) = html_exporter.from_notebook_node(nb)

    # Write the HTML output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_body)
