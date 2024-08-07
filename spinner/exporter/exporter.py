import nbformat
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor


def run_reporter(notebook_path, output_path):
    # Load your notebook
    with open(notebook_path, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # Set up the notebook execution configuration
    execute_preprocessor = ExecutePreprocessor(timeout=600, kernel_name="python3")

    # Execute the notebook
    execute_preprocessor.preprocess(nb, {"metadata": {"path": "./spinner"}})

    # Set up the HTML exporter
    html_exporter = HTMLExporter()
    html_exporter.template_name = "classic"

    # Convert notebook to HTML
    (html_body, resources) = html_exporter.from_notebook_node(nb)

    # Write the HTML output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_body)
