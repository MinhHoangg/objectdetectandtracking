"""Frame source abstractions: video files and live cameras."""

from .base import Frame, FrameSource
from .camera import CameraSource
from .video import VideoSource

__all__ = ["Frame", "FrameSource", "CameraSource", "VideoSource"]
