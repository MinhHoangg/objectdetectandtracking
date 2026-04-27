"""Smoke tests that don't require a model download."""

import json
from pathlib import Path

from object_tracker.config import load_config


CONFIG = Path(__file__).resolve().parents[1] / "config" / "default.json"


def test_load_default_config():
    cfg = load_config(CONFIG)
    assert cfg.model.weights
    assert cfg.tracker.type in {"bytetrack", "botsort"}
    assert cfg.source.kind in {"video", "camera"}
    assert cfg.source.video.path != "" or cfg.source.kind == "camera"
    assert cfg.source.camera.width > 0


def test_config_has_both_source_options():
    raw = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert "video" in raw["source"]
    assert "camera" in raw["source"]
