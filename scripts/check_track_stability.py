"""Track-ID stability check across every video in data/videos/.

Uses config/default.json as-is and reports per-video:
  - frames processed, average FPS
  - per-class: unique track IDs seen, max simultaneous instances,
    ID churn ratio (unique / max-concurrent; 1.0 = perfect, higher = swaps),
    mean ID lifetime in frames, and the actual ID set.

Run:
    uv run python scripts/check_track_stability.py
"""

from __future__ import annotations

import argparse
import time
from collections import Counter, defaultdict
from pathlib import Path

from object_tracker.config import load_config
from object_tracker.detector import Detector
from object_tracker.sources import VideoSource


ROOT = Path(__file__).resolve().parents[1]


def run_video(detector: Detector, video_path: Path) -> dict:
    src = VideoSource(str(video_path))
    frames = 0
    total_dets = 0
    ids_per_class: dict[str, set[int]] = defaultdict(set)
    id_lifetime: Counter[int] = Counter()
    max_concurrent: dict[str, int] = defaultdict(int)

    t0 = time.perf_counter()
    try:
        for frame in src:
            dets = detector.track(frame.image)
            frames += 1
            total_dets += len(dets)

            per_class_now: Counter[str] = Counter()
            for d in dets:
                per_class_now[d.class_name] += 1
                if d.track_id is not None:
                    ids_per_class[d.class_name].add(d.track_id)
                    id_lifetime[d.track_id] += 1
            for cls, n in per_class_now.items():
                if n > max_concurrent[cls]:
                    max_concurrent[cls] = n
    finally:
        src.release()
    elapsed = time.perf_counter() - t0

    classes_summary = {}
    for cls, ids in sorted(ids_per_class.items()):
        ids_sorted = sorted(ids)
        lifetimes = [id_lifetime[i] for i in ids_sorted]
        concurrent = max_concurrent[cls] or 1
        classes_summary[cls] = {
            "unique_ids": len(ids_sorted),
            "id_set": ids_sorted,
            "max_concurrent": max_concurrent[cls],
            "id_churn": round(len(ids_sorted) / concurrent, 2),
            "mean_id_lifetime_frames": (
                round(sum(lifetimes) / len(lifetimes), 1) if lifetimes else 0
            ),
        }

    return {
        "video": video_path.name,
        "size_mb": round(video_path.stat().st_size / 1024 / 1024, 1),
        "resolution": f"{src.width}x{src.height}",
        "src_fps": round(src.fps, 2),
        "frames": frames,
        "elapsed_s": round(elapsed, 2),
        "avg_fps": round(frames / elapsed, 2) if elapsed else 0.0,
        "mean_dets_per_frame": round(total_dets / frames, 2) if frames else 0.0,
        "classes": classes_summary,
    }


def print_report(reports: list[dict], cfg_summary: dict) -> None:
    print("=" * 84)
    print(
        f"  weights={cfg_summary['weights']}  device={cfg_summary['device'] or 'auto'}"
        f"  tracker={cfg_summary['tracker']}  imgsz={cfg_summary['imgsz']}"
        f"  conf={cfg_summary['conf']}"
    )
    print(
        f"  classes={cfg_summary['classes'] or '(all)'}"
        f"   exclude={cfg_summary['exclude'] or '(none)'}"
    )
    print("=" * 84)

    for r in reports:
        print()
        print(f"[{r['video']}] {r['size_mb']} MB  {r['resolution']} @ {r['src_fps']} fps")
        print(
            f"  processed {r['frames']} frames in {r['elapsed_s']}s "
            f"-> {r['avg_fps']} fps   (mean {r['mean_dets_per_frame']} dets/frame)"
        )
        if not r["classes"]:
            print("  no detections")
            continue
        print(
            f"  {'class':<10} {'uniqueIDs':>10} {'maxConc':>8} {'churn':>7} "
            f"{'meanLife(f)':>12}   IDs"
        )
        for cls, s in r["classes"].items():
            ids_str = ",".join(f"#{i}" for i in s["id_set"][:8])
            if len(s["id_set"]) > 8:
                ids_str += f",…(+{len(s['id_set']) - 8})"
            verdict = "✓ stable" if s["id_churn"] <= 1.0 else "✗ swaps"
            print(
                f"  {cls:<10} {s['unique_ids']:>10} {s['max_concurrent']:>8} "
                f"{s['id_churn']:>7} {s['mean_id_lifetime_frames']:>12}   {ids_str}  {verdict}"
            )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, default=ROOT / "config" / "default.json")
    ap.add_argument("--videos-dir", type=Path, default=ROOT / "data" / "videos")
    ap.add_argument("--video", type=Path, default=None,
                    help="Run only on this single video file (overrides --videos-dir)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    print(f"Loading detector ({cfg.model.weights}) ...")
    detector = Detector(cfg.model, cfg.tracker, cfg.classes, cfg.exclude_classes)

    if args.video:
        videos = [args.video]
    else:
        videos = sorted(args.videos_dir.glob("*.mp4"))
    if not videos:
        print(f"No .mp4 files found in {args.videos_dir}")
        return

    reports = []
    for v in videos:
        print(f"\n>>> {v.name} ...")
        reports.append(run_video(detector, v))

    print_report(
        reports,
        {
            "weights": cfg.model.weights,
            "device": cfg.model.device,
            "tracker": cfg.tracker.config_path or cfg.tracker.type,
            "imgsz": cfg.model.imgsz,
            "conf": cfg.model.conf,
            "classes": cfg.classes,
            "exclude": cfg.exclude_classes,
        },
    )


if __name__ == "__main__":
    main()
