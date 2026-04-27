"""End-to-end pipeline: source -> detector/tracker -> visualizer."""

from __future__ import annotations

import json
import time
from pathlib import Path

import cv2

from .config import AppConfig
from .detector import Detection, Detector
from .sources import CameraSource, Frame, FrameSource, VideoSource
from .visualizer import Visualizer


def build_source(cfg: AppConfig) -> FrameSource:
    s = cfg.source
    if s.kind == "video":
        if not s.video.path:
            raise ValueError("source.video.path must be set when source.kind == 'video'")
        return VideoSource(s.video.path)
    if s.kind == "camera":
        c = s.camera
        return CameraSource(c.index, c.width, c.height, c.fps)
    raise ValueError(f"Unknown source kind: {s.kind!r}")


class Pipeline:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.detector = Detector(
            cfg.model,
            cfg.tracker,
            class_filter=cfg.classes,
            exclude=cfg.exclude_classes,
        )
        self.visualizer = Visualizer(
            draw_trails=cfg.output.draw_trails,
            trail_length=cfg.output.trail_length,
        )

    def run(self, source: FrameSource | None = None) -> None:
        owned = source is None
        src = source or build_source(self.cfg)

        writer = self._open_writer(src) if self.cfg.output.save else None
        log_fp = self._open_log()
        window = "object-tracker"
        if self.cfg.output.show:
            cv2.namedWindow(window, cv2.WINDOW_NORMAL)
            w = max(320, int(self.cfg.output.window_width))
            h = max(240, int(self.cfg.output.window_height))
            cv2.resizeWindow(window, w, h)

        last = time.time()
        ema_fps = 0.0
        try:
            for frame in src:
                detections = self.detector.track(frame.image)

                now = time.time()
                inst_fps = 1.0 / max(1e-6, now - last)
                last = now
                ema_fps = inst_fps if ema_fps == 0 else 0.9 * ema_fps + 0.1 * inst_fps

                self._log_detections(log_fp, frame, detections)

                hud = [
                    f"FPS: {ema_fps:5.1f}   frame: {frame.index}",
                    f"detections: {len(detections)}",
                ]
                annotated = self.visualizer.draw(frame.image, detections, hud_lines=hud)

                if writer is not None:
                    writer.write(annotated)
                if self.cfg.output.show:
                    cv2.imshow(window, annotated)
                    if (cv2.waitKey(1) & 0xFF) in (ord("q"), 27):
                        break
                    # Stop if the user closed the window via the 'X' button.
                    try:
                        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                            break
                    except cv2.error:
                        break
        finally:
            if writer is not None:
                writer.release()
            if log_fp is not None:
                log_fp.close()
            if self.cfg.output.show:
                try:
                    cv2.destroyWindow(window)
                except cv2.error:
                    pass
            if owned:
                src.release()

    def _open_writer(self, src: FrameSource) -> cv2.VideoWriter:
        out_dir = Path(self.cfg.output.save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"tracked_{int(time.time())}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = src.fps if src.fps > 0 else 30.0
        return cv2.VideoWriter(str(path), fourcc, fps, (src.width, src.height))

    def _open_log(self):
        path_str = self.cfg.output.log_path
        if not path_str:
            return None
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open("a", encoding="utf-8")

    @staticmethod
    def _log_detections(fp, frame: Frame, detections: list[Detection]) -> None:
        if fp is None or not detections:
            return
        for d in detections:
            x1, y1, x2, y2 = d.bbox
            record = {
                "frame": frame.index,
                "ts_ms": frame.timestamp_ms,
                "track_id": d.track_id,
                "class_id": d.class_id,
                "class_name": d.class_name,
                "confidence": round(d.confidence, 4),
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            }
            fp.write(json.dumps(record) + "\n")
        fp.flush()
