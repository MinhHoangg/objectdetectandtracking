"""Read frames from a connected camera via OpenCV."""

from __future__ import annotations

import time
from typing import Iterator

import cv2

from .base import Frame, FrameSource


class CameraSource(FrameSource):
    def __init__(
        self,
        index: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
    ) -> None:
        self.index = index
        # CAP_DSHOW gives much faster open times on Windows; falls back gracefully.
        backend = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0
        self._cap = cv2.VideoCapture(index, backend)
        if not self._cap.isOpened():
            self._cap = cv2.VideoCapture(index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, fps)
        self.width = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or width
        self.height = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or height
        self.fps = self._cap.get(cv2.CAP_PROP_FPS) or float(fps)

    def __iter__(self) -> Iterator[Frame]:
        idx = 0
        t0 = time.time()
        while True:
            ok, image = self._cap.read()
            if not ok or image is None:
                # Live source: a transient read failure shouldn't kill the loop.
                if not self._cap.isOpened():
                    break
                continue
            ts_ms = (time.time() - t0) * 1000.0
            yield Frame(index=idx, image=image, timestamp_ms=ts_ms)
            idx += 1

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
