"""Drawing helpers: bounding boxes, labels, motion trails, HUD."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Iterable

import cv2
import numpy as np

from .detector import Detection


def _color_for_id(track_id: int | None, class_id: int) -> tuple[int, int, int]:
    seed = (track_id if track_id is not None else class_id) * 2654435761 & 0xFFFFFFFF
    r = (seed >> 16) & 0xFF
    g = (seed >> 8) & 0xFF
    b = seed & 0xFF
    # Boost saturation for visibility on real-world footage.
    return (int(b | 0x40), int(g | 0x40), int(r | 0x40))


class Visualizer:
    def __init__(self, draw_trails: bool = True, trail_length: int = 30) -> None:
        self._draw_trails = draw_trails
        self._trails: dict[int, deque[tuple[int, int]]] = defaultdict(
            lambda: deque(maxlen=trail_length)
        )

    def reset(self) -> None:
        self._trails.clear()

    def draw(
        self,
        frame: np.ndarray,
        detections: Iterable[Detection],
        hud_lines: list[str] | None = None,
    ) -> np.ndarray:
        out = frame  # draw in place; caller passes a frame it owns
        for det in detections:
            x1, y1, x2, y2 = (int(v) for v in det.bbox)
            color = _color_for_id(det.track_id, det.class_id)
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

            tag = (
                f"#{det.track_id} {det.class_name} {det.confidence:.2f}"
                if det.track_id is not None
                else f"{det.class_name} {det.confidence:.2f}"
            )
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(out, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
            cv2.putText(
                out, tag, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA,
            )

            if self._draw_trails and det.track_id is not None:
                cx, cy = det.center
                trail = self._trails[det.track_id]
                trail.append((int(cx), int(cy)))
                for i in range(1, len(trail)):
                    cv2.line(out, trail[i - 1], trail[i], color, 2)

        if hud_lines:
            self._draw_hud(out, hud_lines)
        return out

    @staticmethod
    def _draw_hud(frame: np.ndarray, lines: list[str]) -> None:
        x, y = 10, 22
        for line in lines:
            cv2.putText(
                frame, line, (x + 1, y + 1),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2, cv2.LINE_AA,
            )
            cv2.putText(
                frame, line, (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA,
            )
            y += 22
