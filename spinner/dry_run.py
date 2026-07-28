"""Dry-run mode implementation for Spinner.

This module provides comprehensive dry-run functionality that allows testing
and previewing all operations without executing actual changes.
"""

from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


class DryRunContext:
    """Context manager for dry-run mode operations.
    
    Provides color-coded output, timestamps, and detailed logging of all
    operations that would be executed in normal mode.
    """
    
    def __init__(self, console: Console, enabled: bool = False, verbosity: int = 0):
        """Initialize dry-run context.
        
        Args:
            console: Rich console for output
            enabled: Whether dry-run mode is active
            verbosity: Verbosity level (0=minimal, 1=normal, 2=detailed)
        """
        self.console = console
        self.enabled = enabled
        self.verbosity = verbosity
        self._operation_count = 0
        self._execution_counts = defaultdict(int)  # Track execution counts per parameter set
        self._displayed_params = set()  # Track which parameter sets have been displayed
        self._command_info = {}  # Store command info for final display
        
    def is_enabled(self) -> bool:
        """Check if dry-run mode is enabled."""
        return self.enabled
    
    def _get_timestamp(self) -> str:
        """Get formatted timestamp for logging."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _print_header(self, title: str, style: str = "bold cyan") -> None:
        """Print a section header."""
        if self.enabled:
            self.console.print(f"\n[{style}]{'=' * 80}[/]")
            self.console.print(f"[{style}]{title}[/]")
            self.console.print(f"[{style}]{'=' * 80}[/]\n")
    
    def log_operation(self, operation: str, details: dict[str, Any] = None) -> None:
        """Log a dry-run operation with timestamp.
        
        Args:
            operation: Description of the operation
            details: Optional dictionary of operation details
        """
        if not self.enabled:
            return
            
        self._operation_count += 1
        timestamp = self._get_timestamp()
        
        self.console.print(
            f"[dim]{timestamp}[/] [bold yellow]DRY-RUN[/] "
            f"[cyan]Operation #{self._operation_count}:[/] {operation}"
        )
        
        if details and self.verbosity >= 1:
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Key", style="dim")
            table.add_column("Value")
            
            for key, value in details.items():
                table.add_row(key, str(value))
            
            self.console.print(table)
    
    def log_command(
        self,
        command: str,
        parameters: dict[str, Any] | None = None,
        timeout: float | None = None,
        retry: int | None = None,
        app_name: str | None = None,
    ) -> None:
        """Log a command that would be executed with execution count.
        
        Args:
            command: The command string
            parameters: Command parameters
            timeout: Timeout value if set
            retry: Retry count if set
            app_name: Application name, included in the hash key
        """
        if not self.enabled:
            return
        
        # Create a hashable key from app name + command + parameters for counting.
        # Including app_name ensures that two different applications sharing the
        # same command and parameter set are counted separately.
        if parameters:
            param_key = (app_name, command, tuple(sorted(parameters.items())))
        else:
            param_key = (app_name, command)
        
        # Increment execution count
        self._execution_counts[param_key] += 1
        
        # Store command info for later display
        if param_key not in self._command_info:
            self._command_info[param_key] = {
                'command': command,
                'parameters': parameters,
                'timeout': timeout,
                'retry': retry,
                'timestamp': self._get_timestamp()
            }
        
        # Print command immediately so tests can capture it
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
        """Log expected command results.
        
        Args:
            stdout: Expected stdout
            stderr: Expected stderr
            returncode: Expected return code
            elapsed: Expected elapsed time
        """
        if not self.enabled or self.verbosity < 1:
            return
        
        self.console.print(f"[bold cyan]Expected Result:[/]")
        self.console.print(f"  [dim]Return code:[/] {returncode}")
        self.console.print(f"  [dim]Elapsed:[/] {elapsed:.3f}s")
        if stdout and self.verbosity >= 2:
            self.console.print(f"  [dim]Stdout:[/] {stdout}")
        if stderr and self.verbosity >= 2:
            self.console.print(f"  [dim]Stderr:[/] {stderr}")
    
    def log_file_operation(
        self,
        operation: str,
        path: str,
        details: dict[str, Any] = None,
    ) -> None:
        """Log a file system operation.
        
        Args:
            operation: Type of operation (read, write, delete, etc.)
            path: File path
            details: Additional details about the operation
        """
        if not self.enabled:
            return
        
        timestamp = self._get_timestamp()
        self.console.print(
            f"\n[dim]{timestamp}[/] [bold blue]FILE OPERATION:[/] "
            f"[yellow]{operation}[/] [cyan]{path}[/]"
        )
        
        if details and self.verbosity >= 1:
            for key, value in details.items():
                self.console.print(f"  [dim]{key}:[/] {value}")
    
    def log_database_operation(
        self,
        operation: str,
        details: dict[str, Any] = None,
    ) -> None:
        """Log a database operation.
        
        Args:
            operation: Description of database operation
            details: Operation details
        """
        if not self.enabled:
            return
        
        timestamp = self._get_timestamp()
        self.console.print(
            f"\n[dim]{timestamp}[/] [bold magenta]DATABASE:[/] {operation}"
        )
        
        if details and self.verbosity >= 1:
            for key, value in details.items():
                self.console.print(f"  [dim]{key}:[/] {value}")
    
    def log_network_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] = None,
        data: Any = None,
    ) -> None:
        """Log a network request.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            data: Request data
        """
        if not self.enabled:
            return
        
        timestamp = self._get_timestamp()
        self.console.print(
            f"\n[dim]{timestamp}[/] [bold red]NETWORK:[/] "
            f"[yellow]{method}[/] [cyan]{url}[/]"
        )
        
        if self.verbosity >= 1:
            if headers:
                self.console.print("[dim]Headers:[/]")
                for key, value in headers.items():
                    self.console.print(f"  {key}: {value}")
            
            if data and self.verbosity >= 2:
                self.console.print(f"[dim]Data:[/] {data}")
    
    def log_dataframe_update(
        self,
        row_data: dict[str, Any],
    ) -> None:
        """Log a DataFrame update operation with vertical display."""
        return
    
    def start_summary(self) -> None:
        """Start tracking for summary."""
        if self.enabled:
            self._operation_count = 0
            self._execution_counts.clear()
            self._displayed_params.clear()
            self._command_info.clear()
            self._print_header("DRY-RUN MODE ENABLED", "bold yellow")
            self.console.print(
                "[yellow]No actual operations will be performed.[/]\n"
                "[yellow]All commands and operations will be logged for preview.[/]\n"
            )
    
    def print_summary(self) -> None:
        """Print summary of dry-run operations."""
        if not self.enabled:
            return
        
        # First, display all commands with their execution counts
        if self._command_info:
            self.console.print("\n[bold cyan]Commands to be executed:[/]\n")
            
            for param_key in sorted(self._command_info.keys(), key=lambda k: (k[0] or "", k[1])):
                info = self._command_info[param_key]
                count = self._execution_counts[param_key]
                
                command = info['command']
                parameters = info['parameters']
                
                # Format the count text
                if count == 1:
                    count_text = "1x"
                else:
                    count_text = f"{count}x"
                
                # Show parameters with run count
                if parameters:
                    param_str = ", ".join([f"{k}={v}" for k, v in sorted(parameters.items())])
                    self.console.print(
                        f"[yellow]run ({count_text})[/] "
                        f"[green]{command}[/] [dim]({param_str})[/]"
                    )
                else:
                    self.console.print(
                        f"[yellow]run ({count_text})[/] "
                        f"[green]{command}[/]"
                    )
        
        # Overall summary
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
        self.console.print(
            "\n[bold green]OK[/] Dry-run completed successfully. "
            "No actual changes were made.\n"
        )


@contextmanager
def dry_run_context(console: Console, enabled: bool = False, verbosity: int = 0):
    """Context manager for dry-run operations.
    
    Args:
        console: Rich console for output
        enabled: Whether dry-run mode is active
        verbosity: Verbosity level
        
    Yields:
        DryRunContext instance
    """
    ctx = DryRunContext(console, enabled, verbosity)
    if enabled:
        ctx.start_summary()
    try:
        yield ctx
    finally:
        if enabled:
            ctx.print_summary()


