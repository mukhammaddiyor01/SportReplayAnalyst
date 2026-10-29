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
| Training data | 25 manual boxes, 6 full-frame negatives, 5 uncertain extents, 2 recordings; still insufficient |
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

A separate [full-frame box evaluator](docs/box-detector-evaluation.md) scores reviewed
boxes and explicit negatives at a fixed IoU/confidence operating point. It reports
TP/FP/FN and per-recording precision/recall, separately from center/temporal scoring.
A real CPU run with the preserved smoke checkpoint found 0 matching boxes out
of 25 references, 81 false-positive boxes and predictions on all 6 negative images
at confidence .25 / IoU .5. These are reused development data, not independent
validation; the checkpoint stays rejected. Exact receipts are in the linked guide.

## Four-stage completion plan

These are the owner's four delivery stages. Stage 1 establishes and evaluates the
tracking baseline; stage 2 supplies a useful neural detector and rechecks stage 1.
Do not declare reliable tracking complete before the final detector/tracker pair
passes the frozen evaluation. Stages 3 and 4 depend on that evidence.

| Stage | Current state | Required result |
| --- | --- | --- |
| 1. Reliable tracking across videos | Active; experimental OpenCV baseline only | Verified source-timed observations and bounded recovery on independent recordings |
| 2. Useful YOLO model | Development pipeline works; quality gate not met | A reviewed dataset and trained detector that improves useful tracking over the baseline |
| 3. Table-contact detection | Not started; waiting for tracking and contact evidence | Evaluated contact candidates with explicit uncertainty and duplicate suppression |
| 4. Rally start, end and duration | Not started; waiting for interaction evidence | Evaluated rally intervals with supported boundaries and timing uncertainty |

### 1. Reliable tracking across videos

- Inventory recordings, camera conditions, transformations and prior inspection.
  Keep related clips in one recording group; reserve independent evaluation video.
- Review ball positions, missing/ambiguous intervals and track identity across
  different backgrounds, blur and short occlusions. Separate data review from tuning.
- Freeze evaluation intervals, metrics and numerical acceptance criteria before
  further experiments. Report per-recording counts and denominators, not just totals.
- Evaluate correct/wrong observations, false tracks, gaps in seconds, fragmentation
  and recovery. Keep source indices, dimensions and actual timestamps throughout.
- Test bounded runtime, cancellation, camera-drift handling and observed-only UI.

Completion evidence: a reproducible per-recording report for the selected detector
and tracker meeting the predeclared criteria on independent data. Preserve the
OpenCV baseline and failures. Current results do not meet this gate.

### 2. Useful YOLO model

- Expand visible-extent boxes and explicit full-frame hard negatives; exclude
  uncertainty and obtain independent label review. Keep recording-based splits.
- Freeze dataset versions, local model checksum, training settings, resource bounds,
  detection/association metrics and promotion criteria before training.
- Train locally in the separate PyTorch/Ultralytics environment. The existing fixed
  2-epoch smoke command tests the pipeline; a quality-training protocol still needs
  to be defined and implemented explicitly. Do not silently enlarge that smoke run.
- Measure box detection and false candidates separately from temporal association.
  Compare against OpenCV on the same fixed data, then evaluate untouched recordings.
- Integrate only a qualifying local checkpoint through an adapter and bounded worker;
  verify coordinates, time, cancellation and fallback behavior, then repeat stage 1.

Completion evidence: saved protocol, dataset/checkpoint hashes, comparative results
and verified worker integration. Training completion alone does not pass this gate.
The current smoke checkpoint remains rejected and full_shape_v1 remains active.

### 3. Table-contact detection

- First establish what independent contact evidence the footage actually provides.
  Label contact intervals, racket interactions and ambiguous cases separately.
- Define temporal continuity and table/camera assumptions. A 2D turn, table-plane
  projection or missing observation alone cannot establish a contact.
- Implement plain Python candidate rules only when evidence supports them; preserve
  an uncertain/no-decision result and deduplicate candidates over time.
- Evaluate matched events, missed/false events and source-time error with a matching
  tolerance frozen before evaluation. Only then show supported markers in replay.

Completion evidence: independent contact annotations and a reproducible event report
meeting predeclared criteria. If contact is unobservable, retain no decision; do not
force event labels or claim physical coordinates from airborne image points.

### 4. Rally start, end and duration

- Define start confirmation, tolerated gaps in seconds, supported end evidence,
  resets, editing/camera interruptions and video-boundary truncation before coding.
- Implement isolated per-video rally state in a plain Python service. A lost frame
  does not end a rally; detection absence is different from confirmed termination.
- Return supported start/end times, duration and boundary uncertainty. A clipped
  interval is partial, not a claimed complete rally.
- Test short gaps, false starts, duplicate events, scene cuts, resets and partial
  boundaries. Compare intervals and timing against independently reviewed rallies.
- Add replay navigation and durations only from verified results.

Completion evidence: frozen rally rules, service tests and independent interval/
timing evaluation meeting predeclared criteria, followed by browser verification.

### Immediate next action

[Recording inventory and timing diagnostics](docs/tracking-evaluation.md) now
record prior exposure and source-time loss/reacquisition measurements. Regressions
preserve the existing Getty/Lion observation counts; Lion still has no confirmed
observations on its 30 development frames. These are development checks, not a
fresh independent benchmark.

Continue stages 1–2 with data review. Current labels total 25 visible boxes, 6
full-frame negatives and 5 uncertain extents across 2 already-inspected recordings.
The 2026-10-28 increment is in evaluation/getty-box-expansion.json and
getty-negative-pilot.json; it has not been trained on. The frozen 15-box smoke
experiment remains unchanged. Independent label review and new recording diversity
are still missing. A search-region negative requires full-image review before it
can become a full-frame training negative. No model promotion, contact rules or
rally implementation is justified by the present dataset.

## Verification and limits

```bash
.venv/bin/python -m unittest discover -s tests -v
```

139 automated tests pass without torch, a GPU or model downloads. The annotation
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
