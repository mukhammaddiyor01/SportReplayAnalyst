# Sports Replay Analyst

A local table tennis replay workspace built with Python, OpenCV, FastAPI, Jinja2,
and plain HTML/CSS/JavaScript. Video processing stays on this computer.

## Current behavior

- Local playback, seeking, manual source-coordinate table corners, and validated
  unit-table-plane geometry.
- Bounded background frame inspection, camera-movement estimates, progress,
  cancellation, explicit clearing, and private temporary-file cleanup.
- Experimental temporal ball association and a synchronized image-space 2D trail.
  This is an early bright-moving-blob baseline, not a generally reliable tracker.

Table contacts, rally boundaries, shot classification, scoring, and physical
measurements are not implemented. Image-space tracks are not 3D trajectories.
An airborne ball cannot be mapped to its true table coordinates with a table-plane
homography. A direction change alone does not establish table contact.

## Run locally

Use Python 3.12 and this project's own environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8014
```

Open http://127.0.0.1:8014. Use one Uvicorn worker and keep the server local.
The job directory is exclusively locked by one app instance. Only intended
frontend assets are publicly mounted; videos/results use token-scoped job APIs.

## Review a video and try tracking

1. Choose a browser-playable local clip. Selection alone does not upload it.
2. Pause on a clear frame. Select four table corners clockwise from upper-left,
   using the image or numeric source-coordinate controls.
3. Check calibration. It validates this frame's geometry and derives a coarse
   padded image search window for tracking. That window is not a table homography.
4. Select **Track ball (experimental)** to stream a temporary copy to the local
   server and decode/associate it in a spawned worker process. **Inspect video**
   remains available for inspection without tracking.
5. Play or seek to inspect the cyan trail. Only associated observations are
   rendered; gaps and reinitializations break the line. The current label names
   missing/ambiguous states. Predictions and tentative seeds are never rendered
   as measured points. The checkbox hides the overlay.
6. **Cancel analysis** stops active work. **Clear result** deletes the local copy,
   records, and displayed trail. Your original file is never deleted.

Playback/seek clears manual frame calibration. It retains valid source-coordinate
tracking records for the same video. Replacing/removing the video clears them.
Camera drift blocks unattended table-plane reuse; raw-image tracking does not
stabilize the scene. If source timestamps are estimated or decoded dimensions
mismatch browser playback, the overlay is disabled to avoid false synchronization.

## Limits and privacy

Maximum 100 MiB, 60 seconds, 1920x1080, and 120 FPS. The server counts streamed
bytes and validates actual decoding, not just browser/container metadata.
One receiving/running job is admitted at a time; there is no pending queue.
Inputs and results live outside public assets in ignored private job directories.
Completed artifacts expire after one hour; failed/cancelled copies are removed
once their worker exits. Shutdown/restart ends the review session and removes
orphaned artifacts. Cleanup failures are exposed and retried.

The UI explains retention before sending a local copy. Tokens remain in browser
memory, never URLs or localStorage. Page-exit cleanup is best effort, backed by
server deadlines. No cloud inference, remote fonts, analytics, or model download
is used. Do not commit videos, frames, credentials, weights, or local environments.

## Verification and real-video limitations

```bash
.venv/bin/python -m unittest discover -s tests -v
```

70 automated checks pass across HTTP policies, geometry, decoding, camera evidence,
candidates, association, source timing, isolation, worker lifecycle, and cleanup.
The real supplied 360-frame clip was also exercised through the browser, including
tracking, playback/seek synchronization, ambiguity, overlay toggling, cancellation,
and clearing. These checks do not measure general tracking accuracy.

A small same-video pilot uses approximate manual source centers. The frozen
candidate baseline found nearby candidates for all six held-out visible labels
but produced four extra candidates. Temporal association produced five nearby
observations, no wrong labeled observations, and one withheld ambiguous result.
Three held-out search-region negatives had no associated observations. This sparse
reused pilot is not dense temporal identity or generalization ground truth.

The preview's overhead view, watermark, blur, and estimated camera drift still
limit reliability. The detector can follow clothing or miss small/occluded balls.
No physical contact locations, rallies, or accuracy percentages are inferred.

## Offline diagnostics

```bash
.venv/bin/python -m backend.inspect_video /path/to/clip.mp4
.venv/bin/python -m evaluation.evaluate_ball_candidates /path/to/clip.mp4 --split held_out
.venv/bin/python -m evaluation.evaluate_ball_tracking /path/to/clip.mp4 --split held_out
```

Evaluation verifies the source hash before applying tracked pilot labels. Frame
indices and timestamps stay in source coordinates; FPS fallback is explicit.
The final frame timestamp is not the full container playback duration.

See docs/temporal-tracking.md, docs/ball-candidate-baseline.md,
docs/camera-motion.md, and docs/background-jobs.md for evidence and limitations.
Read AGENTS.md for development rules. Initial setup remains on master; subsequent
verified work belongs only on develop. docs/CONTINUE.md records the resume state.
