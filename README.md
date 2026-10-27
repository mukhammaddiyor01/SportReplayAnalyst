# Sports Replay Analyst

Local analysis of prerecorded table tennis video. Python 3.12, OpenCV, NumPy,
FastAPI/Jinja2 and plain HTML/CSS/JavaScript. Video processing stays on this computer.

## Project status and priority

| Stage | Current state |
| --- | --- |
| Video review | Working: local playback, seeking, actual-source frame stepping |
| Table geometry | Working: manual corners, frame-local calibration, camera-drift checks |
| Background processing | Working: bounded workers, progress, cancel, expiry and cleanup |
| Ball tracking | Experimental OpenCV candidates, temporal association and observed-only 2D trail |
| Neural detector | Optional local YOLO baseline/training/evaluation; no model promoted |
| Training data | 15 manual boxes, 5 uncertain extents, 2 recordings; not a sufficient dataset |
| Contacts and rallies | Not implemented; require stronger ball and independent interaction evidence |

The current bottleneck is ball detection on the edited portrait recording. The
small YOLO smoke-training run completed, but produced many false candidates and
no confirmed observations on evaluated intervals. It is not used by the app.

Keep one critical path: **reviewed data → useful detector → verified temporal
tracking → contact evidence → rally rules**. Complete the next step before adding
another interface, model family or sports feature.

## Run locally

Use Python 3.12 and this project’s own environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8014
```

Open http://127.0.0.1:8014. Use one Uvicorn worker. Port 8000 belongs to another
project in the current workspace; do not stop it. No model is downloaded at startup.

1. Choose a local clip, pause, and mark four table corners clockwise from upper-left.
2. Check calibration, then Track ball. Inspect video only is available in details.
3. Review observed-only trails, missing intervals and source-frame stepping.
4. Clear result removes the temporary local copy; the original remains untouched.

Playback/seek clears manual corners. Camera movement blocks calibration reuse.
An airborne image point cannot be mapped to its real table coordinates using a
table-plane homography. Predictions and missing frames are never measured points.

## Neural-detector workflow

Use the normal app environment for data tools. Prepare exact PNG frames outside
Git, review them at `/labels`, download numeric labels, then export reviewed
images/YOLO text files. Commands and limits: [annotation guide](docs/ball-annotation.md).

Assemble reviewed exports by recording, without a random neighboring-frame split:

```bash
.venv/bin/python -m evaluation.training_dataset --train /path/to/train-export --val /path/to/val-export --output /path/to/dataset
```

Shared recording IDs, source hashes, image hashes, identical decoded pixels and
modified labels are rejected. Related excerpts/transcodes must keep the same
recording ID. The generated data.yaml and dataset.json stay outside Git.

Install requirements-yolo.txt in a **separate** Python 3.12 environment; do not mix
its OpenCV/PyTorch dependencies into the running app environment. Use an explicitly
downloaded local model with a verified SHA256. The fixed development smoke run is:

```bash
python -m evaluation.train_ball_model /path/to/dataset --model /path/to/yolo11n.pt --model-sha256 0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1 --output /path/to/new-training-run
python -m evaluation.evaluate_yolo /path/to/clip.mov --annotations evaluation/lion-validation.json --model /path/to/best.pt --model-sha256 CHECKPOINT_SHA256 --ball-class 0
```

The trainer runs 2 CPU epochs with fixed arguments to test the plumbing. It does
not establish model quality. Training and evaluation are offline, explicit CLI
operations; neither silently changes normal worker tracking. See
[fixed protocol and actual results](docs/model-development.md).

## Next work, in order

1. Expand reviewed boxes, hard negatives and independent recordings. Preserve
   uncertain states, source groups and held-out data; review box extents independently.
2. Freeze a meaningful training/evaluation protocol. Measure candidate coverage,
   false candidates and actual temporal associations separately. Compare against
   the existing OpenCV baseline before integrating a neural detector into workers.
3. Only then define evidence for racket/table interactions and rally boundaries.
   Direction reversal or a missing frame alone is insufficient.

## Verification and limits

```bash
.venv/bin/python -m unittest discover -s tests -v
```

127 automated tests pass without torch, a GPU or model downloads. The annotation
browser→JSON→YOLO export and the real local training/evaluation path were also
exercised. These checks do not establish general tracking accuracy.

Local video limits: 100 MiB, 60 seconds, 1920×1080, 120 FPS. One active worker, no
pending queue. Token-scoped copies/results expire after one hour, explicit clear,
or server shutdown. Failed/cancelled work is cleaned once its worker exits.
Annotation exports/training outputs are explicitly saved local artifacts and
remain until their owner removes them; the job expiry policy does not delete them.
Never commit videos, frames, weights, credentials, caches or environments.

[Current handoff](docs/CONTINUE.md) · [OpenCV evaluation](docs/appearance-detector.md) ·
[YOLO baseline](docs/yolo-benchmark.md) · [Job/privacy rules](docs/background-jobs.md).
Read AGENTS.md before changes. Verified implementation belongs on develop;
master remains at the initial setup. Deployment is outside the current scope.
