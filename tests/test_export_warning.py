import pickle
from types import SimpleNamespace

from spinner.cli.main import _warn_missing_plot_configuration


class DummyApp:
    def __init__(self):
        self.messages = []

    def print(self, message):
        self.messages.append(message)


def _dump_payload(file_obj, payload):
    pickle.dump(payload, file_obj)
    file_obj.seek(0)


def test_warn_missing_plot_configuration_emits_warning(tmp_path):
    data_file = tmp_path / "benchdata.pkl"
    payload = {
        "config": SimpleNamespace(
            applications={
                "with_plot": SimpleNamespace(plot=[{"x_axis": "x", "y_axis": "y"}]),
                "without_plot": SimpleNamespace(plot=[]),
            }
        )
    }
    with data_file.open("wb+") as handle:
        _dump_payload(handle, payload)
        app = DummyApp()

        _warn_missing_plot_configuration(app, handle)

    assert len(app.messages) == 1
    assert "WARNING" in app.messages[0]
    assert "without_plot" in app.messages[0]
    assert "df.head()" in app.messages[0]


def test_warn_missing_plot_configuration_is_silent_when_all_plots_exist(tmp_path):
    data_file = tmp_path / "benchdata.pkl"
    payload = {
        "config": SimpleNamespace(
            applications={
                "app": SimpleNamespace(plot=[{"x_axis": "x", "y_axis": "y"}])
            }
        )
    }
    with data_file.open("wb+") as handle:
        _dump_payload(handle, payload)
        app = DummyApp()

        _warn_missing_plot_configuration(app, handle)

    assert app.messages == []
