def run(*args, **kwargs):
    try:
        from .chat import chat_with_data
    except ImportError as exc:  # pragma: no cover - runtime check
        raise RuntimeError(
            "Export requires optional Jupyter dependencies. "
            "Install with `pip install spinner[exporter]`."
        ) from exc

    return chat_with_data(*args, **kwargs)


__all__ = ["run", "run_ai"]