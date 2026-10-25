# Continue Sports Replay Analyst

Checkpoint: 2026-10-25 (Asia/Seoul).

## Working agreement

Speak Uzbek to the user; code, UI, comments, and documentation are English.
Read AGENTS.md before changing code. Keep increments readable and verified.
Work in SportReplayAnalyst under the user's Desktop Projects, not the unrelated
AI _ Python conversation workspace. Do not modify reference projects or deploy.
The user asked for a human-designed workspace; preserve the current replay desk.

Repository: https://github.com/mukhammaddiyor01/SportReplayAnalyst.git (private).
Git CLI authentication works; the GitHub connector previously returned 404.
Use feat: and fix: commits only. The user authorized small verified commits and
pushes to develop. master must remain at 42a6008 (completed initial setup).
Verify current status and log before continuing; do not discard local changes.

## Completed stages

- AGENTS.md committed before code (3d337ba).
- Minimal FastAPI/Jinja2 setup shared by master/develop (42a6008).
- Bounded video reader and inspection CLI (c8327ab).
- Browser-local playback and manual table geometry (f516509).
- Redesigned replay desk (60490f4).
- Earlier handoff (7c75a4d).
- App-owned spawned worker lifecycle, progress, cancellation, cleanup (2c6b5a4).
- Bounded raw-upload API and authenticated status/cancel/delete (44b1438).
- Browser inspection controls and this updated checkpoint are in the latest UI commit.

Python 3.12 .venv and pinned requirements already exist. No new dependencies were
needed for jobs. Controllers coordinate; OpenCV lives in adapters; table rules are
plain Python services. No database, cloud service, or frontend framework.

## Current behavior

Choose local video creates only a browser object URL. Pause and mark four table
corners clockwise by pointer or numeric coordinates. POST /api/calibration sends
only dimensions/corners and returns validated unit-plane geometry. Playback and
seeking invalidate this frame-local calibration; camera stability is not measured.

Inspect video explicitly streams a temporary copy to the local server, then runs
bounded OpenCV decoding in a spawned process. The UI displays decoded-frame count
and source time, not a fabricated percentage. Cancel stops it; Clear deletes its
retained copy/result. Browser preparation and inspection are separate from ball
analysis. The original selected file is never deleted.

The app owns JobManager via FastAPI lifespan. One active admission slot, no
pending queue, eight retained records maximum, 32 messages per worker queue.
Job-specific routes require a random bearer token (header only). Tokens remain in
browser memory, never URLs/localStorage. Wrong tokens cannot read/cancel/delete
another job. Public responses omit tokens and paths. Private job files are never
mounted as static files. Host/origin restrictions and response policies remain.

See docs/background-jobs.md for endpoints, exact limits, states, and cleanup.
100 MiB, 60 seconds, 1920x1080, 120 FPS; receiving timeout 120 seconds, worker
runtime 180 seconds; cooperative cancellation plus terminate/kill fallback.
Inputs/results live in ignored local-data/jobs with private permissions, expire
one hour after completion, and can be explicitly removed earlier. Failed/cancelled
artifacts are removed after the worker exits. Cleanup failures are visible and
retried. Shutdown/restart ends review and removes old job artifacts. Run only one
Uvicorn worker; a POSIX root lock prevents two owners.

## Verification

33 Python checks passed. They cover real generated videos in spawned processes,
progress, cancellation, crashes, runtime timeout, interrupted/oversized transfers,
access isolation, capacity, expiry, private paths, explicit deletion, startup,
shutdown, cleanup retry, health responsiveness, geometry, reader, and HTTP policies.

User footage: gettyimages-1747255434-640_adpp.mp4 in Downloads. 360 frames,
768x432, about 29.970 FPS, 12.012 seconds. Final frame time 11.978633333333335 s;
no timestamp fallback. In the real browser flow, intermediate progress showed
288 frames / 9.576 s and the final summary showed 360 frames / 11.979 s.
Real Cancel, Clear, and removing a running clip were exercised. Private files were
confirmed removed and the original remained present. Final browser error/warn
logs were empty. Screenshots remain outside Git.

The watermark, overhead view, blur, and apparent camera drift still limit the
sample. No ball model has been selected, no detector/tracker implemented, and no
manually annotated evaluation set exists. No contact/rally accuracy was measured.
Do not conflate video inspection with ball analysis. Table-plane homography
cannot locate an airborne ball on the table; 2D direction changes alone do not
confirm table contact. See docs/video-inspection.md and AGENTS.md.

## Next step

Establish a small, video-appropriate ball detection/tracking baseline using the
real clip. Inspect representative frames and define manually annotated tuning
and held-out segments. Check whether the current footage can support the intended
measurements; request a better fixed-camera clip if necessary. Evaluate camera
motion before reusing calibration across frames. Keep uncertain detections and
predictions distinct. Do not assume a general-purpose detector resolves the ball.
Keep contacts and rally rules as later verified stages after reliable observations.

## Resume

The last server was started at http://127.0.0.1:8014. Check before starting another;
port 8000 belongs to the unrelated Coach App. Never stop that other server.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8014
```

Keep videos, extracted frames, weights, local-data, credentials, and .venv out of
Git. Update this checkpoint after the next verified milestone.
