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
    verbosity: int

    @staticmethod
    def get() -> Self:
        assert _GLOBAL_APP is not None, "app not initialized"
        return _GLOBAL_APP

    def __init__(self, verbosity=0, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.verbosity = verbosity
        self.logger = logging.getLogger("spinner")
        self.logger.debug("App started.")

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

    # Backwards compatibility
    vinfo = vprint
    vvinfo = vvprint

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
