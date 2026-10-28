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

## Logic and ownership

The application follows this existing flow:

`Local clip → bounded job → decoded source frames → OpenCV candidates → temporal association → observed-only trail and gap review`

Manual table corners define geometry and the search region. Camera-drift checks
can block calibration reuse; calibration does not turn airborne observations into
physical table positions. Every tracking result retains source indices and time.

| Responsibility | Existing implementation |
| --- | --- |
| Validate requests and coordinate review | backend/routes.py, backend/inspection_routes.py |
| Bound jobs, progress, cancellation and cleanup | backend/jobs.py, backend/adapters/inspection_worker.py |
| Decode frames with source geometry and timestamps | backend/adapters/video_reader.py |
| Produce candidates and compose tracking | backend/adapters/ball_detector.py, backend/adapters/ball_tracking.py |
| Associate candidates and describe missing intervals | backend/services/ball_tracker.py, backend/services/tracking_review.py |
| Present playback, measured trails and review controls | frontend/templates/, frontend/static/ |

Keep plain tracking rules in services and library/inference operations in adapters.
An observed position, a prediction and an uncertain/missing state remain distinct.
Gap review is a navigation aid, not a detected rally boundary.

The separate development flow is:

`Exact frames → manual review → verified YOLO export → recording-separated dataset → offline training → detector and association evaluation`

Tools under evaluation/ run this flow explicitly. They do not select or replace the
normal worker detector. Current worker behavior remains full_shape_v1.

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

| Order | Deliverable | Required evidence before moving on |
| --- | --- | --- |
| 1 — current | Expand manually reviewed data | Visible box extents reviewed independently; explicit full-frame negatives; uncertainty excluded; recording groups and untouched evaluation data identified |
| 2 | Freeze the next training/evaluation protocol | Dataset/version, recording splits, model checksum, settings, metrics and promotion criteria written before running or tuning |
| 3 | Evaluate detector and temporal tracking | Candidate coverage, false candidates, overflow, correct/wrong associations and gaps reported separately; compare with OpenCV on the same frozen evaluation data |
| 4 | Consider worker integration | A useful result on independent recordings that meets the frozen criteria, plus verified source coordinates, timing, cancellation and runtime bounds |
| 5 | Define contact and rally rules | Independent interaction evidence, explicit uncertainty, event deduplication and time-based rally boundaries supported by labeled examples |

For the next data increment, first inventory recordings and their prior exposure.
Use existing recordings as development material; obtain an independent recording
for fresh evaluation before claiming generalization. Review exact source frames,
then export and verify labels with the existing tools. A search-region negative
cannot become a full-frame YOLO negative unless the entire image is reviewed.
Keep related excerpts and transcodes in the same recording group.

Do not repeat the positive-only 2-epoch smoke run as a quality experiment. Useful
data and frozen criteria come before a larger training run. A direction reversal
or missing observation alone cannot establish a contact or rally end.

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
