"""Typer-based command line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import load_config
from .pipeline import Pipeline

app = typer.Typer(add_completion=False, help="Object detection & tracking.")
console = Console()

DEFAULT_CONFIG = Path("config/default.json")


@app.command()
def run(
    config: Path = typer.Option(DEFAULT_CONFIG, "--config", "-c", help="Path to JSON config."),
    video: Optional[Path] = typer.Option(None, "--video", help="Use a video file as the source."),
    camera: Optional[int] = typer.Option(None, "--camera", help="Use a camera index as the source."),
    weights: Optional[str] = typer.Option(None, "--weights", "-w", help="Override model weights path."),
    device: Optional[str] = typer.Option(None, "--device", help="cpu, 0, cuda:0, mps, ..."),
    conf: Optional[float] = typer.Option(None, "--conf", help="Detection confidence threshold."),
    classes: Optional[str] = typer.Option(
        None, "--classes",
        help="Comma-separated class filter, e.g. 'person,car,fire'. Use 'all' to disable filtering.",
    ),
    exclude: Optional[str] = typer.Option(
        None, "--exclude",
        help="Comma-separated classes to exclude, e.g. 'bench,chair'. Applied after --classes.",
    ),
    tracker: Optional[str] = typer.Option(
        None, "--tracker",
        help="Tracker type: 'bytetrack' or 'botsort'. BoT-SORT uses appearance ReID and is more ID-stable.",
    ),
    tracker_config: Optional[Path] = typer.Option(
        None, "--tracker-config",
        help="Path to a custom tracker yaml (e.g. config/bytetrack_stable.yaml). Overrides --tracker.",
    ),
    no_show: bool = typer.Option(False, "--no-show", help="Disable preview window."),
    save: bool = typer.Option(False, "--save", help="Save annotated video to outputs/."),
    log: Optional[Path] = typer.Option(
        None, "--log",
        help="Append per-detection JSONL records to this file (frame, track_id, class, conf, bbox).",
    ),
) -> None:
    """Run the detection + tracking pipeline."""
    cfg = load_config(config)

    if video is not None and camera is not None:
        raise typer.BadParameter("Use either --video or --camera, not both.")
    if video is not None:
        cfg.source.kind = "video"
        cfg.source.video.path = str(video)
    elif camera is not None:
        cfg.source.kind = "camera"
        cfg.source.camera.index = int(camera)

    if weights:
        cfg.model.weights = weights
    if device is not None:
        cfg.model.device = device
    if conf is not None:
        cfg.model.conf = conf
    if classes is not None:
        cfg.classes = [] if classes.strip().lower() == "all" else [
            c.strip() for c in classes.split(",") if c.strip()
        ]
    if exclude is not None:
        cfg.exclude_classes = [] if exclude.strip().lower() in ("", "none") else [
            c.strip() for c in exclude.split(",") if c.strip()
        ]
    if tracker is not None:
        cfg.tracker.type = tracker.strip().lower()
    if tracker_config is not None:
        cfg.tracker.config_path = str(tracker_config)
    if no_show:
        cfg.output.show = False
    if save:
        cfg.output.save = True
    if log is not None:
        cfg.output.log_path = str(log)

    src_label = (
        cfg.source.video.path if cfg.source.kind == "video"
        else f"camera #{cfg.source.camera.index}"
    )
    console.print("[bold green]object-tracker[/] starting with:")
    console.print(f"  source : {cfg.source.kind} ({src_label})")
    console.print(f"  weights: {cfg.model.weights}  device={cfg.model.device or 'auto'}")
    console.print(f"  tracker: {cfg.tracker.type}")
    console.print(f"  classes: {cfg.classes or '(all)'}")
    console.print(f"  exclude: {cfg.exclude_classes or '(none)'}")
    if cfg.tracker.config_path:
        console.print(f"  tracker-cfg: {cfg.tracker.config_path}")

    Pipeline(cfg).run()


@app.command()
def info(
    config: Path = typer.Option(DEFAULT_CONFIG, "--config", "-c"),
) -> None:
    """Print the resolved configuration and exit."""
    cfg = load_config(config)
    console.print(cfg)


if __name__ == "__main__":
    app()
