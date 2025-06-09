import subprocess
import sys
from pathlib import Path


def test_black_formatting():
    repo_root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "black", "--check", str(repo_root)],
        check=True,
    )
