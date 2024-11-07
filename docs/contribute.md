# Contribute to Spinner

Welcome to the Spinner project! This guide will help you set up your development environment, understand our linting policies, learn how to use Git tags for versioning, and understand how our build automation works.

## Setting Up the Development Environment

To set up your development environment for Spinner, follow these steps:

```sh
python3 -m ensurepip
python3 -m pip install virtualenv
python3 -m virtualenv .venv
source .venv/bin/activate
python3 -m pip install pip --upgrade
python -m pip install -e ".[dev]"
```

This will:

- **Ensure `pip` is installed**.
- **Install `virtualenv`** if it's not already installed.
- **Create a virtual environment** in the `.venv` directory.
- **Activate the virtual environment**.
- **Upgrade `pip`** to the latest version.
- **Install the package** in editable mode along with development dependencies specified in `pyproject.toml`.

## Mandatory Lint Policy

We enforce a mandatory linting policy to maintain code quality and consistency. We recommend adding the following pre-commit hook to automatically format your code before each commit.

### Setting Up the Pre-Commit Hook

Create a file named `pre-commit` in the `.git/hooks/` directory and make it executable:

```sh
touch .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

Add the following content to the `pre-commit` file:

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

# Function to format all Python files using black and isort
format_python_files() {
    if command -v black >/dev/null 2>&1 && command -v isort >/dev/null 2>&1; then
        for file in $(git diff --cached --name-only --diff-filter=ACM "$against" | grep -E '\.py$'); do
            black "$file"
            isort "$file"
            git add "$file"
        done
    else
        echo "black or isort not found, skipping Python file formatting."
    fi
}

# Function to format Jupyter notebooks
format_notebooks() {
    if command -v black >/dev/null 2>&1 && command -v isort >/dev/null 2>&1; then
        for file in $(git diff --cached --name-only --diff-filter=ACM "$against" | grep -E '\.ipynb$'); do
            black "$file"
            isort "$file"
            git add "$file"
        done
    else
        echo "black or isort not found, skipping notebook formatting."
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
format_notebooks
clear_notebook_output

# Check for changes
exec git diff-index --check --cached "$against" --
```

This script will:

- **Format C/C++ files** using `clang-format`.
- **Format Python files and notebooks** using `black` and `isort`.
- **Clear outputs** from Jupyter notebooks to avoid committing unnecessary data.
- **Automatically add the formatted files** back to the commit.

## Versioning with Git Tags

We use Git tags to manage our release versions, which are crucial for packaging and distributing the Spinner project via PyPI.

### Using Git Tags

To create a new Git tag for a release, follow these steps:

1. **Ensure all changes are committed**:

   ```sh
   git add .
   git commit -m "Prepare for release v0.0.2"
   ```

2. **Create a new tag**:

   ```sh
   git tag v0.0.2
   ```

   Replace `v0.0.2` with the appropriate version number.

3. **Push the tag to GitHub**:

   ```sh
   git push origin v0.0.2
   ```

### Best Practices for Tagging

- **Semantic Versioning**: We follow [Semantic Versioning](https://semver.org/) with the format `vMAJOR.MINOR.PATCH` (e.g., `v1.2.3`).
  - **MAJOR** version when you make incompatible API changes.
  - **MINOR** version when you add functionality in a backwards-compatible manner.
  - **PATCH** version when you make backwards-compatible bug fixes.

- **Annotated Tags**: Use annotated tags to include additional metadata such as the tagger name, email, date, and a message.

  ```sh
  git tag -a v0.0.2 -m "Release version 0.0.2"
  ```

- **Consistency**: Always start tags with a `v` to denote version (e.g., `v0.0.2`).

- **Changelog Updates**: Before tagging, update the `CHANGELOG.md` to reflect the changes in the new version.

- **Testing Before Release**: Ensure all tests pass before creating a tag.

## Build Automation with GitHub Actions

Our project uses GitHub Actions to automate the build and deployment process. When a new tag is pushed to the repository, the build bot (GitHub Actions workflow) is triggered to:

- **Build the Package**: Create source and wheel distributions of the package.
- **Publish to PyPI**: Upload the distributions to PyPI using Twine.

### How the Build Bot Works

1. **Trigger**: The workflow is triggered on pushing tags that match the pattern `v*.*.*` (e.g., `v0.0.2`).

2. **Workflow File**: The workflow is defined in `.github/workflows/publish.yml`.

3. **Steps**:
   - **Checkout Code**: Fetches the repository code and tags.
   - **Set Up Python**: Configures the Python environment.
   - **Install Dependencies**: Installs build tools like `build` and `twine`.
   - **Build Package**: Uses `python -m build` to create distributions.
   - **Publish Package**: Uploads the package to PyPI using Twine and the stored PyPI API token.

### Configuring PyPI Credentials

- **PyPI API Token**: The API token for PyPI is stored securely in GitHub Secrets under the name `PYPI_API_TOKEN`.
- **Security**: Never commit API tokens or passwords to the repository.

### Important Notes

- **Ensure Tags are Pushed**: The build bot relies on the Git tags to determine the version. Always push your tags to GitHub.
- **Check Workflow Status**: After pushing a tag, monitor the Actions tab in GitHub to ensure the workflow runs successfully.
- **Test Locally**: Before pushing a tag, you can test the build process locally:

  ```sh
  python -m build
  ```
---

Happy coding!
