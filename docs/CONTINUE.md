# Continue Sports Replay Analyst

Checkpoint: 2026-10-26, dense sequence evaluation after the browser 2D trail milestone.

## Agreement and repository

Speak Uzbek; code, interface, comments, and documentation are English.
Read AGENTS.md before changes. Keep code small/readable and work in verified
increments. Do not modify reference projects or deploy. Preserve the replay desk.

Work in SportReplayAnalyst under the user's Desktop Projects, not the unrelated
AI _ Python conversation workspace. Repository:
https://github.com/mukhammaddiyor01/SportReplayAnalyst.git (private).
Git CLI access works; the GitHub connector previously returned 404.

Active branch is develop. Use feat: and fix: commits only. The user authorized
small verified commits and pushes to develop. master stays at 42a6008; never
advance it without a separate explicit instruction. Check git status/log before
resuming; never discard user changes. Important recent commits:

- 1b91b7a: sampled camera drift and calibration reuse result.
- b7b58e2: frozen bright-ball candidate pilot and approximate manual labels.
- a00ebcd: documentation count clarification.
- 1b9a086: pure Python temporal association service.
- c3fe27b: tracking pipeline, real evaluation, worker mode and API validation.
- Latest UI commit: experimental browser tracking/2D overlay and this checkpoint.

Python 3.12 .venv and pinned requirements exist. No new dependencies were added.
FastAPI/Jinja2/OpenCV plus plain JS; no database, cloud inference, or model weights.

## Current implementation

Choose video opens a browser object URL only. Mark four corners clockwise and
Check calibration validates frame geometry. It derives a padded image rectangle
for experimental tracking; it does not make an airborne point a table coordinate.
Playback/seek clears manual geometry, while tracking results remain source-timed.

Inspect video runs bounded frame inspection and sampled camera drift checks.
Track ball (experimental) additionally runs bright-blob extraction and pure Python
temporal association. The worker returns one record per decoded frame, with source
index/time, status, local track ID, observation/prediction separately, and gap marker.

The browser canvas renders a 0.6s cyan image-space tail of observed associations
only. Predictions, tentative seeds, and ambiguous/missing frames are not plotted;
gaps and new IDs break the line. Presented-video timestamps synchronize playback.
Overlay is disabled if source timing was estimated or source/playback sizes differ.
There is a hide/show checkbox. The system does not stabilize the camera.

BallTracker confirms three consecutive unique moving candidates, gates by source
time/diagonal, avoids size-based selection, withholds close ambiguity/overflow,
retains identity for gaps up to 0.18s, and confirms a new ID after longer losses.
It rejects nonmonotonic inputs before mutating state. No shared global tracker.
These are experimental rules, not proof of ball identity; clothing can still track.

## Jobs and privacy

One app-owned spawned worker at a time, no pending queue, up to eight retained
records, bounded progress queue. Token-scoped status/cancel/delete. Raw-upload
limits: 100 MiB, 60s, 1920x1080, 120 FPS. Receiving timeout 120s; runtime 180s;
cooperative cancellation plus terminate/kill fallback. Keep Uvicorn to one worker.

Copies/results live in ignored private local-data/jobs. Cancel analysis waits for
the worker before cleanup; Clear result removes artifacts and the displayed trail.
Original files are never removed. Completed copies expire after one hour. Shutdown
and restart end review and remove orphaned artifacts under an exclusive root lock.
Cleanup failures are visible/retried. Tokens stay in browser memory, not URLs or
localStorage; leaving the page requests best-effort cleanup backed by deadlines.
Only intended static frontend assets are mounted. No external video/AI transfer.

The job reservation accepts optional mode=track plus search_region; default is
inspect. Schema admission and actual source-size validation are separate. See
docs/background-jobs.md and docs/temporal-tracking.md for exact behavior.

## Verification and real video

70 Python tests passed, including 13 pure temporal tests and new pipeline/worker
mode tests. JavaScript syntax checks passed. Unit rules cover false candidates,
ambiguity, short/long gaps, skipped indices, irregular time, reset/isolation, and
source scaling. Jobs/HTTP/geometry/camera/candidate checks still pass.

User footage: gettyimages-1747255434-640_adpp.mp4 in Downloads. Source hash is in
evaluation/ball-pilot.json. It has 360 frames, 768x432, about 29.970 FPS, 12.012s;
last frame time 11.978633333333335s. The camera estimate found 13.064px maximum
frame-boundary displacement vs 4.406px threshold over 24 supported comparisons.
This is an image-transform estimate, not measured 3D camera movement. Calibration
reuse is blocked; tracking remains raw image-space with an explicit warning.

The 18 approximate manual labels form a tiny adjacent same-video pilot. The frozen
candidate baseline had 6/6 nearby held-out candidates plus 4 extras in 3 ambiguous
frames. Initial frozen temporal rules had 5/6 nearby held-out associated
observations, zero wrong labeled observations, and one withheld ambiguous frame
(210). Three held-out negatives had no associations. Tuning had 6/6 and zero
negative associations. No parameters were adjusted against held-out failure.

The evaluator processes all preceding frames as unlabeled inference context.
This reuses sparse labels; no dense temporal identity, independent generalization,
real occlusion-recovery, or contact/rally accuracy has been measured.

Actual browser flow used a slightly different corner-derived search rectangle:
360 source records, 208 associations, 20 prediction-only frames. Those are runtime
counts, not accuracy. Frame 180 at 6.006s aligned with the visible ball and tail;
frame 210 at 7.007s displayed no observation (ambiguous). Playback, seeking,
overlay toggle, cancellation, and Clear result worked. Cleanup left zero private
job directories and preserved the original file. Final browser error/warn logs
were empty. The latest screenshot stays outside Git with other local UI evidence.

## Dense sequence diagnostic

Added evaluation/ball-sequences.json and evaluate_ball_sequences.py, sharing the
source-record collector with the original sparse evaluator. Two contiguous
30-frame intervals were manually reviewed from source crops; five ambiguous
racket/player frames remain uncertain. The frozen baseline matched 26/26 visible
labels in 140–169 and 29/29 in 230–259 within 8px. Each interval had two correct
runs, zero visible losses, and zero ID changes across continuously visible labels.
This is a single-reviewer same-video diagnostic, not general accuracy; it has no
negative labels and cannot measure ball-absent false tracks. No detector/tracker
parameters changed. The sparse held-out result remains 5/6 with frame 210 withheld.
76 Python tests passed, including six scoring checks. See temporal-tracking.md.

## Next step

Review a dense difficult interval around frame 210 and ball-absent frames to
measure false initializations before changing the detector/tracker. New diagnostic
labels are not an untouched tuning-independent benchmark.

Expand sequence-level manual evaluation before contact/rally inference. Review
false initializations, missed small balls, nearby player/clothing ambiguity,
real occlusions, and identity changes. Obtain a better fixed-camera clip if needed.
Do not retune the frozen baseline against the existing held-out labels without a
new evaluation protocol. Keep measured/associated points separate from predictions.

Contacts, racket interactions, rally timing, event timeline, scoring, physical
speed, and 3D reconstruction are not implemented. Direction changes alone cannot
confirm table contact. Define independent contact evidence and explicit rally
rules before coding those stages. Update this checkpoint after verified work.

## Resume commands

The last local server was 127.0.0.1:8014. Check before starting another. Port 8000
belongs to Coach App; do not stop unrelated servers.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8014
.venv/bin/python -m evaluation.evaluate_ball_tracking /path/to/clip.mp4 --split held_out
```

Keep user footage, frames, results, credentials, weights, and local environments
out of Git. portfolio-assets contains original generated concepts, not screenshots
or proof of tracking quality. No deploy is authorized.
