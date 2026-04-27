"""Read frames from a video file via OpenCV."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import cv2

from .base import Frame, FrameSource


class VideoSource(FrameSource):
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        if not Path(self.path).exists():
            raise FileNotFoundError(f"Video not found: {self.path}")
        self._cap = cv2.VideoCapture(self.path)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open video: {self.path}")
        self.fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def __iter__(self) -> Iterator[Frame]:
        idx = 0
        while True:
            ok, image = self._cap.read()
            if not ok or image is None:
                break
            ts = self._cap.get(cv2.CAP_PROP_POS_MSEC)
            yield Frame(index=idx, image=image, timestamp_ms=ts)
            idx += 1

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
