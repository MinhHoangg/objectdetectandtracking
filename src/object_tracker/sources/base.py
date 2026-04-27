"""Common interface for frame producers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator

import numpy as np


@dataclass
class Frame:
    index: int
    image: np.ndarray  # BGR, HxWx3
    timestamp_ms: float


class FrameSource(ABC):
    """Abstract iterable of :class:`Frame` objects."""

    fps: float = 0.0
    width: int = 0
    height: int = 0

    @abstractmethod
    def __iter__(self) -> Iterator[Frame]: ...

    @abstractmethod
    def release(self) -> None: ...

    def __enter__(self) -> "FrameSource":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
