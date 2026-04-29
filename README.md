# Object Detection & Tracking

A Python application that runs **YOLO (YOLO26 / YOLOv12 / any
Ultralytics-compatible model) + ByteTrack / BoT-SORT** on either a **video file**
or a **live camera**, draws annotated boxes / IDs / motion trails, and
(optionally) saves the result to disk.

The codebase is intentionally focused on **detection + tracking only** — the
downstream consumer (e.g. a UAV follow controller) is handled separately.

---

## Features

- 🔍 **Detection** with [Ultralytics](https://docs.ultralytics.com) YOLO models —
  recommended: [YOLO26](https://docs.ultralytics.com/models/yolo26/) (NMS-free,
  edge-optimized, released Jan 2026); also works with
  [YOLOv12](https://github.com/sunsmarterjie/yolov12), YOLO11, YOLOv8, etc.
- 🎯 **Multi-object tracking** with ByteTrack or BoT-SORT (built into Ultralytics).
- 🎥 **Two input modes**, switchable from the config or CLI:
  - **Video file** (`source.kind = "video"`)
  - **Live camera** (`source.kind = "camera"`)
  - Both have their own block in the config so settings can coexist.
- 🖼️ **Live preview & MP4 export** with bounding boxes, track IDs, motion trails
  and an FPS / detection-count HUD.
- ⚙️ **Single JSON config** (`config/default.json`); every field overridable from the CLI.
- 📦 **Managed with [`uv`](https://docs.astral.sh/uv/)**.

---

## Project structure

```
ObjectDetectAndTracking/
├── pyproject.toml                  # Project metadata + dependencies (uv-managed)
├── README.md                       # ← you are here
├── .kb                             # Knowledge-base map of the codebase
├── config/
│   └── default.json                # Default runtime configuration
├── data/videos/                    # Drop test videos here (git-ignored)
├── models/                         # Drop YOLO weights here (git-ignored)
├── src/object_tracker/             # Importable package
│   ├── __init__.py
│   ├── __main__.py                 # `python -m object_tracker`
│   ├── cli.py                      # Typer CLI (`object-tracker run ...`)
│   ├── config.py                   # JSON -> typed dataclasses
│   ├── detector.py                 # YOLO + tracker wrapper (Ultralytics .track)
│   ├── pipeline.py                 # End-to-end loop: source -> detect/track -> draw
│   ├── visualizer.py               # Boxes, labels, trails, HUD
│   └── sources/
│       ├── base.py                 # FrameSource ABC + Frame dataclass
│       ├── video.py                # OpenCV video-file source
│       └── camera.py               # OpenCV camera source
└── tests/
    └── test_smoke.py               # Config-loading unit tests
```

---

## How it works

```
                ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
 video / cam →  │  FrameSource │ →  │  Detector        │ →  │  Visualizer  │
                │  (OpenCV)    │    │  YOLO + tracker  │    │  HUD/boxes/  │
                └──────────────┘    └──────────────────┘    │   trails     │
                                              │              └──────┬───────┘
                                              ▼                     ▼
                                       List[Detection]         window / .mp4
```

1. `Pipeline.run()` opens a `FrameSource` based on `source.kind`
   (`VideoSource` or `CameraSource`).
2. `Detector.track()` calls `YOLO.track(...)` so detection **and** tracking
   happen in one shot — every detection comes back with a stable `track_id`.
3. `Visualizer` draws boxes, labels, motion trails and a HUD on each frame.
4. The pipeline optionally shows a preview window and writes an annotated
   `.mp4` into `outputs/`.

Each `Detection` exposes:

```python
Detection(track_id, class_id, class_name, confidence, bbox=(x1, y1, x2, y2))
# Properties: .center  -> (cx, cy)
#             .area    -> bbox area in pixels
```

These are the data points another component (e.g. a UAV controller) needs.

---

## Installation

Requires **Python 3.10+** and [`uv`](https://docs.astral.sh/uv/) installed.

### Windows (PowerShell)

```powershell
# from the project root
uv sync
```

### macOS / Linux (bash / zsh)

```bash
# from the project root
uv sync
```

This creates `.venv/` and installs every dependency declared in `pyproject.toml`.

### GPU acceleration

The default `uv sync` installs CPU-only PyTorch. Check what you have and upgrade if needed:

| Platform | Hardware | Install command |
| -------- | -------- | --------------- |
| Windows / Linux | NVIDIA GPU (CUDA 12.4) | `uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124` |
| Windows / Linux | NVIDIA GPU (CUDA 11.8) | `uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118` |
| macOS | Apple Silicon (MPS) | No extra step — PyTorch uses MPS automatically when `device=mps` |
| Any | CPU only | Default after `uv sync` |

> **Verify GPU is visible:**
> ```python
> import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))
> # or on Mac:
> print(torch.backends.mps.is_available())
> ```
> If this returns `False` after installing the CUDA wheel, your driver or CUDA toolkit may be missing.

Then use the right `--device` flag:

| Value | Meaning |
| ----- | ------- |
| `cpu` | Always works, slowest |
| `0` | First NVIDIA GPU (requires CUDA) |
| `0,1` | Multi-GPU |
| `mps` | Apple Silicon GPU (macOS only) |

### Running CLI commands

**Windows PowerShell** uses a backtick `` ` `` for line continuation:
```powershell
uv run object-tracker run `
    --video data/videos/sample.mp4 `
    --device cpu
```

**macOS / Linux bash** uses a backslash `\`:
```bash
uv run object-tracker run \
    --video data/videos/sample.mp4 \
    --device cpu
```

### Get a model

- **Default (YOLO26 — Ultralytics native)**: the config points at
  `models/yolo26n.pt`. This is the YOLO26 weight shipped by Ultralytics and is
  guaranteed to match the installed `ultralytics` package. It will
  auto-download on first run, or grab it from
  <https://huggingface.co/Ultralytics/YOLO26> and drop it in `models/`.
- **YOLOv12 "turbo" weights** (from <https://github.com/sunsmarterjie/yolov12>)
  use an older `AAttn(qk, v)` layout and will fail to load on Ultralytics 8.4+
  with `AttributeError: 'AAttn' object has no attribute 'qkv'`. Use
  `yolo12n.pt` (Ultralytics) instead, or pin `ultralytics<8.4`.
- **Other Ultralytics weights**: pass `--weights <path-or-name>` to override
  (e.g. `--weights yolov8n.pt` for auto-downloaded YOLOv8n).
- **Fire / smoke detection**: train or download a custom YOLO model whose
  class names include `fire` / `smoke`. The COCO models do not contain them.

---

## Usage

The CLI is registered as `object-tracker` (and as `python -m object_tracker`):

```powershell
# 1) Run on a test video (uses YOLO12 weights from config: models/yolo12n.pt)
uv run object-tracker run --video data/videos/sample.mp4

# 2) Switch to a live camera (index 0 = default webcam)
uv run object-tracker run --camera 0

# 3) Force the GPU
uv run object-tracker run --device 0 --video data/videos/sample.mp4

# 4) Filter classes from the CLI
uv run object-tracker run --camera 0 --classes "person,car,truck"

# 5) Save an annotated MP4 to outputs/
uv run object-tracker run --video data/videos/sample.mp4 --save --no-show

# 6) Inspect the resolved configuration
uv run object-tracker info
```

Press **`q`** or **Esc** in the preview window to stop.

### CLI flags

| Flag | Purpose |
| ---- | ------- |
| `--config / -c` | Path to a JSON config (default `config/default.json`). |
| `--video PATH` | Use a video file as the source (sets `source.kind=video`). |
| `--camera N` | Use camera index `N` (sets `source.kind=camera`). |
| `--weights PATH` | Override `model.weights`. |
| `--device STR` | `cpu`, `0`, `cuda:0`, `mps`, … |
| `--conf FLOAT` | Detection confidence threshold. |
| `--classes a,b,c` | Keep only these classes (or `all`). |
| `--exclude a,b,c` | Drop these classes (applied after `--classes`). |
| `--tracker NAME` | `bytetrack` or `botsort`. BoT-SORT uses appearance ReID and is more ID-stable. |
| `--tracker-config PATH` | Use a custom tracker yaml (overrides `--tracker`). See `config/bytetrack_stable.yaml`. |
| `--save` | Write an annotated `.mp4` into `outputs/`. |
| `--no-show` | Headless mode (useful on a Pi / Jetson). |
| `--log PATH` | Append one JSON record per detection per frame to `PATH` (JSONL). |

---

## Configuration (`config/default.json`)

The config holds **two input blocks** so you can keep settings for both ready,
and a single `kind` switch picks which one is used:

```json
{
    "source": {
        "kind": "video",         // "video" | "camera"
        "video":  { "path": "data/videos/sample.mp4" },
        "camera": { "index": 0, "width": 1280, "height": 720, "fps": 30 }
    }
}
```

Other top-level sections (mapped 1:1 to dataclasses in
[`src/object_tracker/config.py`](src/object_tracker/config.py)):

- `model` — weights path, image size, confidence, IoU, device, FP16.
- `classes` — allow-list of class names (empty = keep everything).
- `exclude_classes` — drop-list applied after `classes` (e.g. `["bench"]`).
- `tracker` — `type` (`bytetrack`/`botsort`), `persist`, optional `config_path` to a custom tracker yaml.
- `output` — show window, save video, motion-trail length, `window_width`/`window_height` (initial preview size).

CLI flags always win over the JSON file.

---

## Improving track-ID stability

If the same person keeps getting a new track ID (common on dim CCTV, low FPS,
or heavy occlusion), try these in order:

1. **Lower the detection threshold** so the person isn't dropped on borderline
   frames:
   ```powershell
   uv run object-tracker run --video data/videos/bucket11.mp4 --conf 0.20
   ```
2. **Use the bundled "stable" ByteTrack profile** (longer `track_buffer`,
   looser association). Keeps IDs alive ~3 seconds at 30 FPS instead of ~1:
   ```powershell
   uv run object-tracker run --video data/videos/bucket11.mp4 \
       --tracker-config config/bytetrack_stable.yaml
   ```
3. **Switch to BoT-SORT with appearance ReID** — best for re-identifying a
   person who walks behind something and reappears:
   ```powershell
   uv run object-tracker run --video data/videos/bucket11.mp4 \
       --tracker-config config/botsort_stable.yaml
   ```
4. **Use a bigger detector** (`yolo12s.pt` / `yolo12m.pt`) — fewer missed
   detections → fewer ID switches. Slower per frame.

Tunable knobs inside the tracker yamls
([config/bytetrack_stable.yaml](config/bytetrack_stable.yaml),
[config/botsort_stable.yaml](config/botsort_stable.yaml)):

| Knob | Effect |
| ---- | ------ |
| `track_buffer` | Frames a lost track is kept alive before a new ID is assigned. ↑ = stickier IDs. |
| `match_thresh` | IoU+motion match threshold. ↓ = more lenient re-association. |
| `new_track_thresh` | Confidence required to spawn a brand-new ID. ↑ = fewer spurious IDs. |
| `track_high_thresh` / `track_low_thresh` | First/second-pass detection thresholds used by ByteTrack. |
| `with_reid` (BoT-SORT) | Enable appearance-based re-identification. |

---

## Training your own model (e.g. fire / smoke)

The COCO-pretrained `yolo12n.pt` does **not** know about `fire` or `smoke`. To
detect custom classes you need to fine-tune YOLO on a labeled dataset.

### 1. Get a labeled dataset

The dataset must be in **YOLO format** (one `.txt` per image, each line
`class_id cx cy w h` normalized to `[0, 1]`):

```
dataset/
├─ images/
│  ├─ train/  *.jpg
│  └─ val/    *.jpg
└─ labels/
   ├─ train/  *.txt   # same filename as the image
   └─ val/    *.txt
```

Ready-made fire/smoke datasets:
- **D-Fire** — <https://github.com/gaiasd/DFireDataset>
- **Roboflow Universe** — search "fire smoke" and export in *YOLOv8* format.

Then create a `dataset.yaml`:

```yaml
path: D:/datasets/fire-smoke
train: images/train
val:   images/val
names:
  0: fire
  1: smoke
```

### 2. Train (fine-tune from `yolo12n.pt`)

**Windows PowerShell:**
```powershell
uv run yolo detect train `
    model=models/yolo26n.pt `
    data=dataset.yaml `
    epochs=100 `
    imgsz=640 `
    batch=16 `
    device=cpu `
    project=runs/train `
    name=fire-smoke-v1
```

**macOS / Linux:**
```bash
uv run yolo detect train \
    model=models/yolo26n.pt \
    data=dataset.yaml \
    epochs=100 \
    imgsz=640 \
    batch=8 \
    device=0 \
    project=runs/train \
    name=fire-smoke-v1
```

**No GPU (CPU only)** — replace `device=0` with `device=cpu`. Slow but works on any machine:
```powershell
uv run yolo detect train model=models/yolo12n.pt data=dataset.yaml epochs=100 imgsz=640 batch=4 device=cpu project=runs/train name=fire-smoke-v1
```

> On **Apple Silicon Mac** use `device=mps` for ~5× speed vs CPU.

Key args:
- `model=` start from a pretrained checkpoint (transfer learning, much faster).
  Use a bigger one (`yolo26s.pt`, `yolo26m.pt`) for higher accuracy.
- `imgsz=` 640 is a good default; raise to 960/1280 for small/distant objects.
- `batch=` reduce if you OOM (try `8` → `4` → `2`). With `device=cpu`, use `4`.
- `epochs=` 50–300 typical. Watch the validation mAP curve; stop when it plateaus.

Resulting weights: `runs/train/fire-smoke-v1/weights/best.pt`.

> **Re-running training never overwrites previous results.** If `runs/train/fire-smoke-v1`
> already exists, Ultralytics automatically creates `runs/train/fire-smoke-v12`,
> `fire-smoke-v13`, etc. Each run is preserved. To explicitly start fresh, either
> delete the old folder or use a different `name=` value.

### 3. Use the trained model

**Windows:**
```powershell
Copy-Item runs/train/fire-smoke-v1/weights/best.pt models/fire-smoke.pt
uv run object-tracker run --video data/videos/roomfire41.mp4 `
    --weights models/fire-smoke.pt --classes "fire,smoke"
```

**macOS / Linux:**
```bash
cp runs/train/fire-smoke-v1/weights/best.pt models/fire-smoke.pt
uv run object-tracker run --video data/videos/roomfire41.mp4 \
    --weights models/fire-smoke.pt --classes "fire,smoke"
```

> **Want fire/smoke as the new default?** Update `config/default.json` so you
> don't need to pass `--weights` / `--classes` every time:
> ```json
> "model": { "weights": "models/fire-smoke.pt", ... },
> "classes": ["fire", "smoke"],
> ```
> After that, a plain `uv run object-tracker run --video ...` will use your
> trained model automatically.

### 4. Tips for better accuracy

- **More & varied data beats more epochs.** Add hard negatives (rooms with no
  fire, sun glare, orange lights) to cut false positives.
- **Augment aggressively** — Ultralytics enables mosaic/HSV/flip by default;
  add `degrees=10 translate=0.1 scale=0.5 mosaic=1.0` for sparse data.
- **Validate on real footage**, not just held-out dataset images:
  ```powershell
  uv run yolo detect val model=models/fire-smoke.pt data=.../dataset.yaml
  ```
- **Iterate**: review false positives/negatives in `runs/train/.../val_batch*.jpg`,
  add the failure cases to the training set, re-train.
- **Export** to ONNX/TensorRT for deployment speed:
  ```powershell
  uv run yolo export model=models/fire-smoke.pt format=onnx
  ```

---

## Programmatic use

```python
from object_tracker.config import load_config
from object_tracker.pipeline import Pipeline

cfg = load_config("config/default.json")
cfg.source.kind = "camera"
cfg.source.camera.index = 0

Pipeline(cfg).run()
```

To consume detections directly (e.g. to feed your own follow controller):

```python
from object_tracker.config import load_config
from object_tracker.detector import Detector
from object_tracker.pipeline import build_source

cfg = load_config("config/default.json")
detector = Detector(cfg.model, cfg.tracker, cfg.classes)

with build_source(cfg) as src:
    for frame in src:
        for det in detector.track(frame.image):
            print(det.track_id, det.class_name, det.bbox)
```

---

## Development

```powershell
uv run pytest                  # run smoke tests
uv run ruff check src tests    # lint
uv run python -m object_tracker info
```

---

## Credits

- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) — detection & tracking runtime.
- [YOLO26](https://docs.ultralytics.com/models/yolo26/) — Ultralytics' latest NMS-free, edge-optimized YOLO (Jan 2026).
- [YOLOv12 by sunsmarterjie](https://github.com/sunsmarterjie/yolov12) — model architecture & weights.
- [OpenCV](https://opencv.org) — frame I/O and rendering.

## License

MIT.

## SAMPLE CLI COMMAND
> uv run object-tracker run --video data/videos/bucket11.mp4 --classes "fire" --exclude "bench,chair" --tracker-config config/bytetrack_stable.yaml

```powershell
Copy-Item runs/train/fire-smoke-v1/weights/best.pt models/fire-smoke.pt
uv run object-tracker run --video data/videos/roomfire41.mp4 `
    --weights models/fire-smoke.pt --classes "fire,smoke" --tracker-config config/bytetrack_stable.yaml
```