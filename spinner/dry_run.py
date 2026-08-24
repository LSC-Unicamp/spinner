"""Dry-run mode for Spinner."""

from collections import defaultdict
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.table import Table


class DryRunContext:
    def __init__(self, console: Console, enabled: bool = False, verbosity: int = 0):
        self.console = console
        self.enabled = enabled
        self.verbosity = verbosity
        self._execution_counts = defaultdict(int)
        self._command_info = {}
        self._output_name: str | None = None

    def _print_header(self, title: str, style: str = "bold cyan") -> None:
        if self.enabled:
            self.console.print(f"\n[{style}]{'=' * 80}[/]")
            self.console.print(f"[{style}]{title}[/]")
            self.console.print(f"[{style}]{'=' * 80}[/]\n")

    def log_command(
        self,
        command: str,
        app_name: str,
        parameters: dict[str, Any] | None = None,
        timeout: float | None = None,
        retry: int | None = None,
        benchmark_name: str | None = None,
    ) -> None:
        if not self.enabled:
            return

        # Key includes benchmark_name and app_name so that two benchmarks (or
        # two apps) sharing the same command+params are never collapsed into one entry.
        if parameters:
            param_key = (benchmark_name, app_name, command, tuple(sorted(parameters.items())))
        else:
            param_key = (benchmark_name, app_name, command)

        self._execution_counts[param_key] += 1

        if param_key not in self._command_info:
            self._command_info[param_key] = {
                'benchmark_name': benchmark_name,
                'command': command,
                'parameters': parameters,
            }

        self.console.print(f"[bold cyan]COMMAND:[/] [green]{command}[/]")
        if parameters and self.verbosity >= 1:
            self.console.print(f"[dim]Parameters:[/] {parameters}")
        if timeout is not None and self.verbosity >= 1:
            self.console.print(f"[dim]Timeout:[/] {timeout}s")
        if retry is not None and self.verbosity >= 1:
            self.console.print(f"[dim]Retry:[/] {retry}")

    def log_expected_result(
        self,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
        elapsed: float = 0.0,
    ) -> None:
        if not self.enabled or self.verbosity < 1:
            return

        self.console.print(f"[bold cyan]Expected Result:[/]")
        self.console.print(f"  [dim]Return code:[/] {returncode}")
        self.console.print(f"  [dim]Elapsed:[/] {elapsed:.3f}s")
        if stdout and self.verbosity >= 2:
            self.console.print(f"  [dim]Stdout:[/] {stdout}")
        if stderr and self.verbosity >= 2:
            self.console.print(f"  [dim]Stderr:[/] {stderr}")

    def set_output_name(self, name: str) -> None:
        self._output_name = name

    def start_summary(self) -> None:
        if self.enabled:
            self._execution_counts.clear()
            self._command_info.clear()
            self._print_header("DRY-RUN MODE ENABLED", "bold yellow")
            self.console.print(
                "[yellow]No actual operations will be performed.[/]\n"
                "[yellow]All commands and operations will be logged for preview.[/]\n"
            )

    def print_summary(self) -> None:
        if not self.enabled:
            return

        if self._command_info:
            self.console.print("\n[bold cyan]Commands to be executed:[/]\n")

            # Sort by (benchmark_name, app_name, command); None sorts first.
            for param_key in sorted(self._command_info.keys(), key=lambda k: (k[0] or "", k[1] or "", k[2])):
                info = self._command_info[param_key]
                count = self._execution_counts[param_key]
                benchmark_name = info['benchmark_name']
                command = info['command']
                parameters = info['parameters']
                count_text = f"{count}x"
                prefix = f"[dim]{benchmark_name}[/] " if benchmark_name is not None else ""
                if parameters:
                    param_str = ", ".join([f"{k}={v}" for k, v in sorted(parameters.items())])
                    self.console.print(
                        f"{prefix}[yellow]run ({count_text})[/] "
                        f"[green]{command}[/] [dim]({param_str})[/]"
                    )
                else:
                    self.console.print(
                        f"{prefix}[yellow]run ({count_text})[/] "
                        f"[green]{command}[/]"
                    )

        self._print_header("DRY-RUN SUMMARY", "bold yellow")

        total_executions = sum(self._execution_counts.values())
        unique_param_sets = len(self._execution_counts)

        summary_table = Table(show_header=False, box=None)
        summary_table.add_column("Metric", style="bold cyan")
        summary_table.add_column("Value", style="white")
        summary_table.add_row("Unique Parameter Sets", str(unique_param_sets))
        summary_table.add_row("Total Executions", str(total_executions))
        summary_table.add_row("Verbosity Level", str(self.verbosity))

        self.console.print(summary_table)
        if self._output_name is not None:
            self.console.print(f"[dim]Would save results to:[/] {self._output_name}")
        self.console.print(
            "\n[bold green]OK[/] Dry-run completed successfully. "
            "No actual changes were made.\n"
        )


@contextmanager
def dry_run_context(console: Console, enabled: bool = False, verbosity: int = 0):
    ctx = DryRunContext(console, enabled, verbosity)
    if enabled:
        ctx.start_summary()
    try:
        yield ctx
    finally:
        if enabled:
            ctx.print_summary()


