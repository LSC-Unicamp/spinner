import subprocess
import sys
from pathlib import Path


def pytest_sessionstart(session):
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "black", "--check", str(repo_root)], check=True
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "isort",
            "--check-only",
            str(repo_root),
        ],
        check=True,
    )
