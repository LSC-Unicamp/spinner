# io-testbed

![Logo](spinner.svg)

## Setting up environment

```sh
python3 -m virtualenv .venv
pip install -r spinner/requirements.txt
source .venv/bin/activate
```

## Running
```sh
python3 spinner/main.py -b F -r T -c spinner/bench_settings.json -e F
```

# Mandatory development policy
`.git/hooks/pre-commit`
```sh
#!/bin/bash

if git rev-parse --verify HEAD >/dev/null 2>&1; then
    against=HEAD
else
    # Initial commit: diff against an empty tree object
    against=4b825dc642cb6eb9a060e54bf8d69288fbee4904
fi

# Function to format all C/C++ files using clang-format
format_c_cpp_files() {
    if command -v clang-format >/dev/null 2>&1; then
        for file in $(git diff --cached --name-only --diff-filter=ACM "$against" | grep -E '\.(c|h|cpp|hpp)$'); do
            clang-format -i "$file"
            git add "$file"
        done
    else
        echo "clang-format not found, skipping C/C++ file formatting."
    fi
}

# Function to format all Python files using black
format_python_files() {
    if command -v black >/dev/null 2>&1; then
        for file in $(git diff --cached --name-only --diff-filter=ACM "$against" | grep -E '\.py$'); do
            black "$file"
            git add "$file"
        done
    else
        echo "black not found, skipping Python file formatting."
    fi
}

# Function to clear output in Jupyter notebooks
clear_notebook_output() {
    if command -v jupyter >/dev/null 2>&1; then
        for notebook in $(git diff --cached --name-only --diff-filter=ACM "$against" | grep -E '\.ipynb$'); do
            jupyter nbconvert --ClearOutputPreprocessor.enabled=True --inplace "$notebook"
            git add "$notebook"
        done
    else
        echo "jupyter not found, skipping Jupyter notebook output clearing."
    fi
}

# Run the formatting functions
format_c_cpp_files
format_python_files
clear_notebook_output

# Check for changes
exec git diff-index --check --cached "$against" --
```
