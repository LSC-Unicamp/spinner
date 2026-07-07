import pytest

from spinner.app import SpinnerApp


@pytest.fixture(autouse=True)
def reset_global_app():
    """Reset the global SpinnerApp singleton state after each test.

    Prevents test-order contamination caused by tests that call the CLI
    (e.g. via CliRunner) and leave dry_run=True on the singleton.
    """
    yield
    app = SpinnerApp.get()
    app._dry_run = False
    app.verbosity = 0
