def run(*args, **kwargs):
    try:
        from .exporter import run_reporter
    except ImportError as exc:  # pragma: no cover - runtime check
        raise RuntimeError(
            "Export requires optional Jupyter dependencies. "
            "Install with `pip install spinner[notebook]`."
        ) from exc

    return run_reporter(*args, **kwargs)


__all__ = ["run"]
