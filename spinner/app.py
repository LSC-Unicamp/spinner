import logging
import os
from typing import Self

import click
from rich.console import Console
from rich.logging import RichHandler

# ==============================================================================
# GLOBALS
# ==============================================================================

DEFAULT_LOG_LEVEL = os.environ.get("LOGLEVEL", "warning").upper()

# ==============================================================================
# CLASSES
# ==============================================================================


class SpinnerApp(Console):
    _verbosity: int

    @staticmethod
    def get() -> Self:
        assert _GLOBAL_APP is not None, "app not initialized"
        return _GLOBAL_APP

    def __init__(self, verbosity=0, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger("spinner")
        self.verbosity = verbosity
        self.logger.debug("App started.")

    @property
    def verbosity(self) -> int:  # type: ignore[override]
        return self._verbosity

    @verbosity.setter
    def verbosity(self, value: int) -> None:  # type: ignore[override]
        self._verbosity = value
        level_name = os.environ.get("LOGLEVEL", DEFAULT_LOG_LEVEL)
        if value > 0 and "LOGLEVEL" not in os.environ:
            level_name = "INFO"
        level = getattr(logging, level_name.upper(), logging.WARNING)
        root = logging.getLogger()
        self.logger.setLevel(level)
        root.setLevel(level)
        for handler in root.handlers:
            handler.setLevel(level)

    def __del__(self) -> None:
        self.logger.debug("App finished.")

    def vprint(self, *args, **kwargs) -> None:
        """Log a message when verbosity >= 1."""
        if self.verbosity >= 1:
            self.logger.info(*args, **kwargs)

    def vvprint(self, *args, **kwargs) -> None:
        """Log a message when verbosity >= 2."""
        if self.verbosity >= 2:
            self.logger.info(*args, **kwargs)

    def debug(self, *args, **kwargs) -> None:
        self.logger.debug(*args, **kwargs)

    def info(self, *args, **kwargs) -> None:
        self.logger.info(*args, **kwargs)

    def warning(self, *args, **kwargs) -> None:
        self.logger.warning(*args, **kwargs)

    def error(self, *args, **kwargs) -> None:
        self.logger.error(*args, **kwargs)

    def fatal(self, *args, **kwargs) -> None:
        self.logger.fatal(*args, **kwargs)

    def exception(self, *args, **kwargs) -> None:
        self.logger.exception(*args, **kwargs)


_GLOBAL_APP = SpinnerApp()

# ==============================================================================
# LOGGER CONFIGURATION
# ==============================================================================

# NOTE: We need to pass a console (e.g. SpinnerApp) to the RichHandler so that we can
# use logging functions while inside a progress bar context.
logging.basicConfig(
    level=DEFAULT_LOG_LEVEL,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            DEFAULT_LOG_LEVEL,
            _GLOBAL_APP,
            omit_repeated_times=False,
            rich_tracebacks=True,
            tracebacks_suppress=[click],
        ),
    ],
)
