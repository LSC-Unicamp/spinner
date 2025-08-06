def run(*args, **kwargs):
    try:
        from .exporter import run_reporter
    except ImportError as exc:  # pragma: no cover - runtime check
        raise RuntimeError(
            "Export requires optional Jupyter dependencies. "
            "Install with `pip install spinner[exporter]`."
        ) from exc

    return run_reporter(*args, **kwargs)


from .ai_exporter import run_ai_exporter as run_ai

__all__ = ["run", "run_ai"]
