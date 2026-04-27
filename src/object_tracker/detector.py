"""Detection + tracking wrapper around an Ultralytics YOLO model.

Works with any Ultralytics-compatible weight, including YOLOv8/11/12.
For YOLOv12 (https://github.com/sunsmarterjie/yolov12), download a release
weight (e.g. ``yolov12n.pt``) into ``models/`` and point ``model.weights`` at it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .config import ModelConfig, TrackerConfig


@dataclass
class Detection:
    track_id: int | None
    class_id: int
    class_name: str
    confidence: float
    # xyxy in pixel coordinates of the input frame.
    bbox: tuple[float, float, float, float]

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox
        return (0.5 * (x1 + x2), 0.5 * (y1 + y2))

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.bbox
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


class Detector:
    """Loads a YOLO model and runs detection + tracking on frames."""

    def __init__(
        self,
        model_cfg: ModelConfig,
        tracker_cfg: TrackerConfig,
        class_filter: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
    ) -> None:
        # Imported lazily so `--help` / config loading don't pay the torch import cost.
        from ultralytics import YOLO

        self._model = YOLO(model_cfg.weights)
        self._cfg = model_cfg
        self._tracker_yaml = self._resolve_tracker(tracker_cfg)
        self._persist = tracker_cfg.persist

        # Build class id -> name map from the loaded model and resolve the filter.
        self.names: dict[int, str] = dict(self._model.names) if hasattr(self._model, "names") else {}
        wanted = {c.lower() for c in (class_filter or [])}
        excluded = {c.lower() for c in (exclude or [])}
        if wanted:
            ids = [cid for cid, name in self.names.items() if str(name).lower() in wanted]
        else:
            ids = list(self.names.keys())
        if excluded:
            ids = [cid for cid in ids if str(self.names.get(cid, "")).lower() not in excluded]
        # If allow-list/exclude combine to empty, fall back to no filter (don't silently drop everything).
        if wanted or excluded:
            self._class_ids: list[int] | None = ids if ids else None
        else:
            self._class_ids = None

    @staticmethod
    def _resolve_tracker(tracker_cfg: TrackerConfig) -> str:
        # A custom yaml takes priority over the built-in name.
        if tracker_cfg.config_path:
            from pathlib import Path

            p = Path(tracker_cfg.config_path)
            if not p.exists():
                raise FileNotFoundError(f"tracker.config_path not found: {p}")
            return str(p)
        kind = (tracker_cfg.type or "bytetrack").lower()
        if kind not in {"bytetrack", "botsort"}:
            raise ValueError(f"Unknown tracker type: {kind}")
        return f"{kind}.yaml"

    def track(self, image: np.ndarray) -> list[Detection]:
        """Run detect+track on a single BGR frame, returning detections with track ids."""
        results = self._model.track(
            source=image,
            imgsz=self._cfg.imgsz,
            conf=self._cfg.conf,
            iou=self._cfg.iou,
            device=self._cfg.device or None,
            half=self._cfg.half,
            classes=self._class_ids,
            tracker=self._tracker_yaml,
            persist=self._persist,
            verbose=False,
        )
        if not results:
            return []
        r = results[0]
        boxes = getattr(r, "boxes", None)
        if boxes is None or boxes.shape[0] == 0:
            return []

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        clss = boxes.cls.cpu().numpy().astype(int)
        ids = (
            boxes.id.cpu().numpy().astype(int)
            if getattr(boxes, "id", None) is not None
            else np.full(len(xyxy), -1, dtype=int)
        )

        out: list[Detection] = []
        for bb, cf, cl, tid in zip(xyxy, confs, clss, ids):
            out.append(
                Detection(
                    track_id=int(tid) if tid >= 0 else None,
                    class_id=int(cl),
                    class_name=self.names.get(int(cl), str(int(cl))),
                    confidence=float(cf),
                    bbox=(float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])),
                )
            )
        return out
