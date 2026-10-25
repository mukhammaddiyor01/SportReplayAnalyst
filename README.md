# Sports Replay Analyst

Local table tennis replay analysis, built incrementally with Python, OpenCV,
FastAPI, Jinja2, and plain browser JavaScript.

## Current stage

The replay workspace, bounded local video reader, manual frame calibration, and
background video inspection are implemented. Ball
tracking, table-contact estimation, and rally timing are not implemented. No analysis results are fabricated.

## Run locally

Use Python 3.12. Install dependencies in this project's own environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8014
```

Open http://127.0.0.1:8014. Do not expose this development server publicly.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Only frontend static files are public. Videos, extracted frames, weights, and
local environments must remain untracked. The first version targets one fixed
camera and a visible table surface, with manually selected table corners.
Image-space motion is not a 3D trajectory. An airborne ball cannot be mapped to
its true table coordinates using a table-plane homography.

The supplied preview clip has a watermark, overhead perspective, blur, and
apparent camera drift. It has not been validated for contact or rally accuracy.
See AGENTS.md for stage boundaries and the master/develop workflow.

## Inspect a local video

```bash
.venv/bin/python -m backend.inspect_video /path/to/clip.mp4
```

The reader checks at most 100 MiB, 60 seconds, 1920x1080, and 120 FPS.
It decodes sequentially without keeping a video in memory, retains original
frame indices and dimensions, and reports timestamp fallback usage. Invalid or
non-increasing presentation times use an explicitly marked FPS-based estimate.
That estimate does not recover missing source timestamps or establish variable
frame rate accuracy. Metadata and actual decoded dimensions/frame budget are
both checked. Premature EOF relative to declared frame count is rejected;
OpenCV cannot distinguish every corrupt EOF when frame-count metadata is absent.
The final frame timestamp is not the container's total playback duration.

The CLI runs locally outside HTTP. Bounded local video inspection uploads are
available through the inspection job API; this does not perform ball analysis.
See docs/video-inspection.md for the real-clip evidence and remaining limits.

## Prepare and calibrate a clip

1. Choose a local browser-playable video. Playback does not upload the video.
2. Pause at a clear frame and select the four table corners clockwise from the
   upper-left, using the video or numeric source-coordinate controls.
3. Select **Check calibration**. Only corners and source dimensions go to the
   local server. It validates a convex, sufficiently large quadrilateral and
   computes a table-plane homography to a unit square.
4. Playback, seeking, removing, or replacing the clip clears the frame calibration.
   Undoing a corner also invalidates the previous geometry check.

The browser checks size, duration, and resolution; it does not reliably expose
source FPS. Run the separate local inspection command to validate all frames
and FPS. Browser preparation is not admission to an analysis job.
The calibration response has no persistent identifier and is not saved. It is
valid only for the selected frame; camera drift has not been evaluated. A unit
square describes the table plane, not physical distances or airborne positions.
Use **Inspect video** to send a temporary copy to the local server and inspect
all frames in a worker process. **Cancel inspection** stops the worker and removes
its copy. **Clear inspection** deletes the retained copy and result. Ball analysis remains a later stage.

## Background video inspection

The app owns one spawned worker process at a time, with decoded-frame progress,
cancellation, runtime limits, and private job storage. Completed copies/results
expire after one hour; failed/cancelled copies are removed after the worker stops.
Shutdown/restart ends the review session and removes orphaned job files. The
original selected file is never deleted. Run a single Uvicorn worker.
See docs/background-jobs.md for lifecycle, retention, and HTTP endpoints.

Inspection displays actual decoded-frame progress and timing, followed by a real
summary. It does not measure ball detection, contacts, or rallies. The browser
explains local retention before inspection begins. File replacement and page exit
request cleanup; exit requests are best effort, backed by server deadlines.
Tokens stay in browser memory, never URLs or localStorage. A page reload cannot
recover old results. Stop/restart ends the review session and clears old artifacts.

33 automated checks pass. Real browser checks on the supplied preview confirmed
progress, 360 decoded frames, cancellation, explicit clearing, and replacing an
active clip. See docs/background-jobs.md for evidence and limits.
