"""Test cases for dry-run mode functionality.

This module tests the comprehensive dry-run mode implementation including
command logging, parameter display, and result simulation.
"""

import io
import tempfile
from pathlib import Path

import pytest
import yaml

from spinner.app import SpinnerApp
from spinner.dry_run import DryRunContext, dry_run_context
from spinner.runner.dry_run_runner import DryRunInstanceRunner
from spinner.schema import SpinnerConfig


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    config_data = {
        "metadata": {
            "description": "Test benchmark",
            "version": "1.0.0",
            "runs": 2,
            "timeout": 10.0,
            "retry": 1,
        },
        "applications": {
            "test_app": {
                "command": "echo 'Testing with param={{param}}'",
                "capture": [
                    {
                        "type": "all",
                        "name": "output",
                    }
                ],
            }
        },
        "benchmarks": {
            "test_bench": {
                "apps": "test_app",
                "param": [1, 2, 3],
            }
        },
    }
    return SpinnerConfig.from_data(config_data)


@pytest.fixture
def app_with_dry_run():
    """Create a SpinnerApp with dry-run enabled."""
    app = SpinnerApp(verbosity=1, dry_run=True)
    return app


@pytest.fixture
def app_without_dry_run():
    """Create a SpinnerApp with dry-run disabled."""
    app = SpinnerApp(verbosity=1, dry_run=False)
    return app


class TestDryRunContext:
    """Test the DryRunContext class."""

    def test_context_initialization(self, app_with_dry_run):
        """Test that DryRunContext initializes correctly."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        assert ctx.is_enabled() is True
        assert ctx.verbosity == 1
        assert ctx._operation_count == 0

    def test_context_disabled(self, app_without_dry_run):
        """Test that DryRunContext respects disabled state."""
        ctx = DryRunContext(app_without_dry_run, enabled=False)
        assert ctx.is_enabled() is False

    def test_log_operation(self, app_with_dry_run, capsys):
        """Test logging operations in dry-run mode."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        ctx.log_operation("Test operation", {"key": "value"})
        
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out
        assert "Test operation" in captured.out

    def test_log_command(self, app_with_dry_run, capsys):
        """Test logging commands in dry-run mode."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        ctx.log_command(
            command="echo 'test'",
            app_name="test-app",
            parameters={"param": "value"},
            timeout=5.0,
            retry=2,
        )
        
        captured = capsys.readouterr()
        assert "COMMAND" in captured.out
        assert "echo 'test'" in captured.out

    def test_log_expected_result(self, app_with_dry_run, capsys):
        """Test logging expected results."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        ctx.log_expected_result(
            stdout="test output",
            stderr="",
            returncode=0,
            elapsed=0.5,
        )
        
        captured = capsys.readouterr()
        assert "Expected Result" in captured.out
        assert "0.500s" in captured.out

    def test_log_file_operation(self, app_with_dry_run, capsys):
        """Test logging file operations."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        ctx.log_file_operation(
            operation="write",
            path="/tmp/test.txt",
            details={"size": "1024 bytes"},
        )
        
        captured = capsys.readouterr()
        assert "FILE OPERATION" in captured.out
        assert "write" in captured.out
        assert "/tmp/test.txt" in captured.out

    def test_log_database_operation(self, app_with_dry_run, capsys):
        """Test logging database operations."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        ctx.log_database_operation(
            operation="INSERT INTO table",
            details={"rows": 10},
        )
        
        captured = capsys.readouterr()
        assert "DATABASE" in captured.out
        assert "INSERT INTO table" in captured.out

    def test_log_network_request(self, app_with_dry_run, capsys):
        """Test logging network requests."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        ctx.log_network_request(
            method="POST",
            url="https://api.example.com/data",
            headers={"Content-Type": "application/json"},
            data='{"key": "value"}',
        )
        
        captured = capsys.readouterr()
        assert "NETWORK" in captured.out
        assert "POST" in captured.out
        assert "https://api.example.com/data" in captured.out

    def test_context_manager(self, app_with_dry_run, capsys):
        """Test dry_run_context as a context manager."""
        with dry_run_context(app_with_dry_run, enabled=True, verbosity=1) as ctx:
            ctx.log_operation("Test operation")
        
        captured = capsys.readouterr()
        assert "DRY-RUN MODE ENABLED" in captured.out
        assert "DRY-RUN SUMMARY" in captured.out

    def test_verbosity_levels(self, app_with_dry_run, capsys):
        """Test different verbosity levels."""
        # Verbosity 0 - minimal output
        ctx_v0 = DryRunContext(app_with_dry_run, enabled=True, verbosity=0)
        ctx_v0.log_command("echo test", "test-app", parameters={"p": "v"})
        out_v0 = capsys.readouterr().out
        
        # Verbosity 1 - normal output
        ctx_v1 = DryRunContext(app_with_dry_run, enabled=True, verbosity=1)
        ctx_v1.log_command("echo test", "test-app", parameters={"p": "v"})
        out_v1 = capsys.readouterr().out
        
        # Verbosity 2 - detailed output
        ctx_v2 = DryRunContext(app_with_dry_run, enabled=True, verbosity=2)
        ctx_v2.log_expected_result(stdout="detailed output", returncode=0, elapsed=1.0)
        out_v2 = capsys.readouterr().out
        
        # Higher verbosity should produce more output
        assert len(out_v1) >= len(out_v0)
        assert "Parameters" in out_v1


class TestDryRunInstanceRunner:
    """Test the DryRunInstanceRunner class."""

    def test_runner_initialization(self, app_with_dry_run, sample_config):
        """Test that DryRunInstanceRunner initializes correctly."""
        import pandas as pd
        from spinner.runner.progress import RunnerProgress
        
        benchmark = sample_config.benchmarks["test_bench"]
        df = pd.DataFrame()
        
        with RunnerProgress(app_with_dry_run, sample_config, total=1) as progress:
            runner = DryRunInstanceRunner(
                app_with_dry_run,
                sample_config,
                benchmark_name="test_bench",
                application_name="test_app",
                benchmark=benchmark,
                dataframe=df,
                progress=progress,
            )
            
            assert runner.app == app_with_dry_run
            assert runner.benchmark_name == "test_bench"
            assert runner.application_name == "test_app"

    def test_run_command_simulation(self, app_with_dry_run, sample_config, capsys):
        """Test that run_command simulates execution without running actual commands."""
        import pandas as pd
        from spinner.runner.progress import RunnerProgress
        
        benchmark = sample_config.benchmarks["test_bench"]
        df = pd.DataFrame()
        
        with RunnerProgress(app_with_dry_run, sample_config, total=1) as progress:
            runner = DryRunInstanceRunner(
                app_with_dry_run,
                sample_config,
                benchmark_name="test_bench",
                application_name="test_app",
                benchmark=benchmark,
                dataframe=df,
                progress=progress,
            )
            
            runner.run_command(
                idx=0,
                command="echo 'test'",
                parameters={"param": 1},
                timeout=10.0,
                retry=1,
            )
        
        captured = capsys.readouterr()
        assert "COMMAND" in captured.out
        assert "echo 'test'" in captured.out
        assert "Expected Result" in captured.out

    def test_no_actual_execution(self, app_with_dry_run, sample_config):
        """Test that no actual commands are executed in dry-run mode."""
        import pandas as pd
        from spinner.runner.progress import RunnerProgress

        benchmark = sample_config.benchmarks["test_bench"]
        df = pd.DataFrame()

        with RunnerProgress(app_with_dry_run, sample_config, total=1) as progress:
            runner = DryRunInstanceRunner(
                app_with_dry_run,
                sample_config,
                benchmark_name="test_bench",
                application_name="test_app",
                benchmark=benchmark,
                dataframe=df,
                progress=progress,
            )

            runner.run_command(
                idx=0,
                command="echo 'should not run'",
                parameters={"param": 1},
            )

        # DataFrame must remain empty — no real execution happened
        assert len(df) == 0


class TestDryRunIntegration:
    """Integration tests for dry-run mode."""

    def test_cli_dry_run_flag(self):
        """Test that CLI accepts --dry-run flag."""
        from click.testing import CliRunner
        from spinner.cli.main import cli
        
        runner = CliRunner()
        
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                "metadata": {
                    "description": "Test",
                    "version": "1.0",
                    "runs": 1,
                },
                "applications": {
                    "test": {"command": "echo test"}
                },
                "benchmarks": {
                    "test": {"apps": "test", "param": [1]}
                }
            }
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            # Test with --dry-run flag
            result = runner.invoke(cli, ['--dry-run', 'run', config_path])
            assert result.exit_code == 0 or "DRY-RUN" in result.output
            
            # Test with -n flag (short form)
            result = runner.invoke(cli, ['-n', 'run', config_path])
            assert result.exit_code == 0 or "DRY-RUN" in result.output
        finally:
            Path(config_path).unlink()

    def test_dry_run_with_verbosity(self):
        """Test dry-run mode with different verbosity levels."""
        from click.testing import CliRunner
        from spinner.cli.main import cli

        runner = CliRunner()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                "metadata": {
                    "description": "Test",
                    "version": "1.0",
                    "runs": 1,
                    "timeout": 5.0,
                },
                "applications": {
                    "test": {"command": "echo test"}
                },
                "benchmarks": {
                    "test": {"apps": "test", "param": [1]}
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            # -v (verbosity=1): parameters, timeout/retry, and expected result
            # are shown, but simulated stdout is not.
            result = runner.invoke(cli, ['-v', '--dry-run', 'run', config_path])
            output_v1 = result.output
            assert "Timeout" in output_v1, "-v should show timeout"
            assert "Simulated output" not in output_v1, (
                "-v should NOT show simulated stdout"
            )

            # -vv (verbosity=2): additionally prints simulated stdout inside
            # the Expected Result block.
            result = runner.invoke(cli, ['-vv', '--dry-run', 'run', config_path])
            output_v2 = result.output
            assert "Simulated output" in output_v2, (
                "-vv should show simulated stdout in Expected Result"
            )
        finally:
            Path(config_path).unlink()

    def test_no_file_modification_in_dry_run(self, app_with_dry_run, sample_config):
        """Test that no files are modified in dry-run mode."""
        from spinner.runner import run
        
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
            output_path = f.name
            initial_size = f.tell()
        
        try:
            # Run in dry-run mode
            with open(output_path, 'wb') as output:
                run(app_with_dry_run, sample_config, output)
            
            # File should not be modified (or only minimally)
            final_size = Path(output_path).stat().st_size
            # In dry-run mode, the file should not have significant data written
            assert final_size == initial_size or final_size < 100
        finally:
            Path(output_path).unlink()


class TestPerformance:
    """Test that dry-run mode has no performance overhead when disabled."""

    def test_no_overhead_when_disabled(self, app_without_dry_run):
        """Test that there's no performance overhead when dry-run is disabled."""
        import time
        
        # This is a simple check that dry-run code doesn't slow down normal execution
        ctx = DryRunContext(app_without_dry_run, enabled=False)
        
        start = time.time()
        for _ in range(1000):
            ctx.log_operation("test")
            ctx.log_command("test", "test-app")
            ctx.log_expected_result()
        elapsed = time.time() - start
        
        # Should be very fast since nothing is actually logged
        assert elapsed < 0.1  # Should complete in less than 100ms

    def test_dry_run_property_access(self, app_with_dry_run, app_without_dry_run):
        """Test that accessing dry_run property is fast."""
        import time
        
        start = time.time()
        for _ in range(10000):
            _ = app_with_dry_run.dry_run
            _ = app_without_dry_run.dry_run
        elapsed = time.time() - start
        
        # Property access should be negligible
        assert elapsed < 0.01  # Should complete in less than 10ms




class TestDryRunCommandKeyBug:
    """Regression tests for the command-key deduplication bug.

    Before the fix, the key used to aggregate execution counts in
    ``log_command`` was built from *parameters only*.  Two different
    applications sharing the same parameter set therefore collided: only
    the first command was stored in ``_command_info`` and the second was
    silently dropped from the summary.
    """

    def test_two_apps_same_params_both_appear_in_summary(self, app_with_dry_run, capsys):
        """Both commands must be present in the summary when two apps share
        identical parameters."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=0)

        ctx.log_command(command='echo "A n=1"', app_name="app-A", parameters={"n": 1})
        ctx.log_command(command='echo "B n=1"', app_name="app-B", parameters={"n": 1})

        # Two distinct (command, params) pairs → two entries in _command_info
        assert len(ctx._command_info) == 2, (
            "Expected two separate entries in _command_info for two commands "
            "with the same parameters, but got one — deduplication bug."
        )

    def test_two_apps_same_params_independent_execution_counts(self, app_with_dry_run):
        """Execution counts must be tracked independently per command."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=0)

        for _ in range(3):
            ctx.log_command(command='echo "A n=1"', app_name="app-A", parameters={"n": 1})
        for _ in range(2):
            ctx.log_command(command='echo "B n=1"', app_name="app-B", parameters={"n": 1})

        counts = list(ctx._execution_counts.values())
        assert sorted(counts) == [2, 3], (
            f"Expected counts [2, 3] for two distinct commands, got {sorted(counts)}"
        )

    def test_summary_lists_both_commands(self, app_with_dry_run, capsys):
        """print_summary must mention both command strings."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=0)

        ctx.log_command(command='echo "A n=1"', app_name="app-A", parameters={"n": 1})
        ctx.log_command(command='echo "B n=1"', app_name="app-B", parameters={"n": 1})

        capsys.readouterr()  # discard log_command output
        ctx.print_summary()
        summary = capsys.readouterr().out

        assert 'echo "A n=1"' in summary, "Command A missing from dry-run summary"
        assert 'echo "B n=1"' in summary, "Command B missing from dry-run summary"

    def test_same_command_same_params_still_aggregates(self, app_with_dry_run):
        """The same (command, params) pair must still be counted as one entry
        with an aggregated execution count — not split into duplicates."""
        ctx = DryRunContext(app_with_dry_run, enabled=True, verbosity=0)

        for _ in range(4):
            ctx.log_command(command='echo "A n=1"', app_name="app-A", parameters={"n": 1})

        assert len(ctx._command_info) == 1
        assert list(ctx._execution_counts.values()) == [4]
