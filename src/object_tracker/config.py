"""Typed configuration loader (JSON -> dataclasses).

The config exposes both a `video` and a `camera` block so users can keep
their settings for both inputs side-by-side. The active one is selected by
`source.kind` (`"video"` or `"camera"`), which is also overridable from the CLI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints


@dataclass
class ModelConfig:
    weights: str = "yolov8n.pt"
    imgsz: int = 640
    conf: float = 0.35
    iou: float = 0.5
    device: str = ""
    half: bool = False


@dataclass
class TrackerConfig:
    type: str = "bytetrack"  # "bytetrack" | "botsort"
    persist: bool = True
    config_path: str = ""  # optional path to a custom <tracker>.yaml; overrides `type` if set


@dataclass
class VideoSourceConfig:
    path: str = ""


@dataclass
class CameraSourceConfig:
    index: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30


@dataclass
class SourceConfig:
    kind: str = "video"  # "video" | "camera"
    video: VideoSourceConfig = field(default_factory=VideoSourceConfig)
    camera: CameraSourceConfig = field(default_factory=CameraSourceConfig)


@dataclass
class OutputConfig:
    show: bool = True
    save: bool = False
    save_dir: str = "outputs"
    draw_trails: bool = True
    trail_length: int = 30
    log_path: str = ""  # if set, append JSONL detection records here
    window_width: int = 1280
    window_height: int = 720


@dataclass
class AppConfig:
    model: ModelConfig = field(default_factory=ModelConfig)
    classes: list[str] = field(default_factory=list)
    exclude_classes: list[str] = field(default_factory=list)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    source: SourceConfig = field(default_factory=SourceConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def _from_dict(cls, data: Any):
    if not is_dataclass(cls):
        return data
    if not isinstance(data, dict):
        raise TypeError(f"Expected mapping for {cls.__name__}, got {type(data).__name__}")
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        if f.name not in data or data[f.name] is None:
            continue
        ftype = hints.get(f.name, f.type)
        value = data[f.name]
        if is_dataclass(ftype):
            kwargs[f.name] = _from_dict(ftype, value)
            continue
        if get_origin(ftype) is list:
            (inner,) = get_args(ftype) or (Any,)
            if is_dataclass(inner) and isinstance(value, list):
                kwargs[f.name] = [_from_dict(inner, item) for item in value]
                continue
        kwargs[f.name] = value
    return cls(**kwargs)


def load_config(path: str | Path) -> AppConfig:
    """Load an :class:`AppConfig` from a JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    with p.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError(f"Config root must be a JSON object, got {type(raw).__name__}")
    return _from_dict(AppConfig, raw)
