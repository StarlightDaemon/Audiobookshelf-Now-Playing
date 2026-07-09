"""Round-trip and validation tests for app.config."""

import app.config as config
from app.config import AppConfig


def _use_tmp_config(monkeypatch, tmp_path):
    path = str(tmp_path / "config.json")
    monkeypatch.setattr(config, "_CONFIG_PATH", path)
    return path


def test_load_config_defaults_when_file_missing(monkeypatch, tmp_path):
    _use_tmp_config(monkeypatch, tmp_path)
    cfg = config.load_config()
    assert cfg == AppConfig()


def test_save_then_load_roundtrip(monkeypatch, tmp_path):
    _use_tmp_config(monkeypatch, tmp_path)
    original = AppConfig(
        layout="portrait-dogear", theme="parchment", label="Now Listening",
        corners="square",
    )
    config.save_config(original)
    loaded = config.load_config()
    assert loaded == original


def test_load_config_rejects_invalid_layout(monkeypatch, tmp_path):
    path = _use_tmp_config(monkeypatch, tmp_path)
    import json
    with open(path, "w") as f:
        json.dump({"layout": "not-a-real-layout", "theme": "kraft",
                   "label": "Reading", "corners": "rounded"}, f)
    cfg = config.load_config()
    assert cfg.layout == "landscape-classic"
    assert cfg.theme == "kraft"  # other valid fields are preserved


def test_load_config_rejects_invalid_theme(monkeypatch, tmp_path):
    path = _use_tmp_config(monkeypatch, tmp_path)
    import json
    with open(path, "w") as f:
        json.dump({"layout": "portrait-cover", "theme": "not-a-real-theme",
                   "label": "Reading", "corners": "rounded"}, f)
    cfg = config.load_config()
    assert cfg.theme == "github-dark"


def test_load_config_rejects_invalid_corners(monkeypatch, tmp_path):
    path = _use_tmp_config(monkeypatch, tmp_path)
    import json
    with open(path, "w") as f:
        json.dump({"layout": "portrait-cover", "theme": "light",
                   "label": "Reading", "corners": "triangular"}, f)
    cfg = config.load_config()
    assert cfg.corners == "rounded"


def test_load_config_rejects_blank_label(monkeypatch, tmp_path):
    path = _use_tmp_config(monkeypatch, tmp_path)
    import json
    with open(path, "w") as f:
        json.dump({"layout": "portrait-cover", "theme": "light",
                   "label": "   ", "corners": "rounded"}, f)
    cfg = config.load_config()
    assert cfg.label == "Currently Reading"


def test_load_config_handles_malformed_json(monkeypatch, tmp_path):
    path = _use_tmp_config(monkeypatch, tmp_path)
    with open(path, "w") as f:
        f.write("{not valid json")
    cfg = config.load_config()
    assert cfg == AppConfig()


def test_save_config_writes_expected_json(monkeypatch, tmp_path):
    path = _use_tmp_config(monkeypatch, tmp_path)
    config.save_config(AppConfig(layout="portrait-spine", theme="light",
                                  label="Reading", corners="square"))
    import json
    with open(path) as f:
        data = json.load(f)
    assert data == {
        "layout": "portrait-spine", "theme": "light",
        "label": "Reading", "corners": "square",
    }
