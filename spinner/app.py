import logging
from rich.console import Console


class SpinnerApp(Console):
    verbosity: int

    def __init__(self, verbosity, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.verbosity = verbosity
        self.logger = logging.getLogger("spinner")

    def vprint(self, *args, **kwargs) -> None:
        if self.verbosity >= 1:
            self.print(*args, **kwargs)

    def vvprint(self, *args, **kwargs) -> None:
        if self.verbosity >= 2:
            self.print(*args, **kwargs)

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
