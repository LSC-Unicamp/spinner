from click.testing import CliRunner
from spinner.cli.main import cli


def test_dry_run():
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["run", "config.yml", "--dry-run"]
    )

    assert result.exit_code == 0
    assert "DRY RUN MODE" in result.output
    assert "No benchmarks will be executed" in result.output
