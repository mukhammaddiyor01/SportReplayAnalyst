# Continue Sports Replay Analyst

Checkpoint saved on 2026-10-24 (Asia/Seoul). The user asked to preserve today's
progress and continue tomorrow. Do not infer an automatic scheduled run.

## User preferences and scope

Talk to the user in Uzbek. Keep code, interface, comments, and documentation in
English. Read AGENTS.md before changes. Build readable, small, verified increments
without drifting from local table tennis video analysis. The user requested a
more intentional, human-designed interface; the replay desk redesign is complete.
Do not change the reference projects or deploy this application.

## Repository and Git

Repository: https://github.com/mukhammaddiyor01/SportReplayAnalyst.git (private).
Local project folder is named SportReplayAnalyst under the user's Desktop Projects.
Use this repository, not the unrelated AI _ Python conversation workspace.
Git CLI access succeeded even though the GitHub connector returned 404.
Use only feat: and fix: prefixes. Review staged files and commit each verified
logical step. User authorization covers pushes in the agreed branch workflow.

- Active branch: develop, synchronized with origin at the checkpoint.
- master: 42a6008, the completed initial setup. Do not advance it again.
- 3d337ba: development rules, committed before application code.
- 42a6008: minimal local FastAPI/Jinja2 application setup.
- c8327ab: bounded OpenCV reader with source timestamps and inspection CLI.
- f516509: browser-local playback and manual frame calibration.
- 60490f4: replay workspace and calibration inspector redesign.
- Working tree was clean before saving this handoff.

## Implemented behavior

Python 3.12 virtual environment in .venv; pinned direct dependencies in
requirements.txt and development dependencies in requirements-dev.txt.
FastAPI controllers, OpenCV adapters, plain Python geometry service, and plain
HTML/CSS/JavaScript. No database, cloud inference, or frontend framework.

- GET / serves the replay workspace; GET /health returns status.
- Only frontend/static is mounted publicly. Host checks, no-store responses,
  and restrictive browser policies are configured.
- CLI: python -m backend.inspect_video /path/to/clip.mp4.
- Reader limits: 100 MiB, 60 seconds, 1920x1080, 120 FPS; checks actual decoded
  frames and source dimensions, with explicit fallback for unusable timestamps.
- Choose video uses a browser object URL. Video bytes are not uploaded or saved.
- Playback controls and seeking work; selecting a file reads browser metadata.
- Four corners can be clicked or entered numerically in source coordinates.
- POST /api/calibration receives dimensions and corners only. Validates winding,
  convexity, area, bounds, and finite coordinates; returns a unit-plane homography.
- Playback, seeking, replacement, and removal clear the frame calibration.
- The visible corner count and empty-state hint update with selection/reset.
- The redesigned UI prioritizes the video and attached calibration inspector,
  with local assets, keyboard controls, and responsive stacking.

## Real footage and evidence

User-supplied file: gettyimages-1747255434-640_adpp.mp4, in the user's Downloads.
Do not commit or transmit the video or derived frames to external services.
All 360 frames decoded at 768x432. Approximately 29.970 FPS and 12.012-second
container duration. Last frame timestamp: 11.978633333333335 seconds. No FPS
fallback was required. See docs/video-inspection.md.

The overhead view, watermark, motion blur, and apparent camera drift limit its
suitability. Camera stability is not evaluated. Do not call it a validated
stationary-camera clip. Image-space tracks are not 3D trajectories. Table-plane
homography cannot recover true table coordinates of an airborne ball. A change
in image direction alone is insufficient evidence for a table contact.

14 Python tests passed. Browser checks with the supplied real clip verified
selection, metadata, numeric corners, pointer coordinate mapping, geometry
submission, playback/reset, seeking/reset, removal/reselection, and the live
corner counter. Desktop and narrow layouts were reviewed. Browser error/warn
logs were empty during calibration. See docs/calibration-verification.md and
docs/design-direction.md. Do not imply a manually annotated evaluation exists.

## Not implemented yet

No video uploads, background analysis jobs, progress/cancellation, automated
ball detection/tracking, trajectory overlays, table-contact events, rally timing,
or event timeline. No detection, contact, or rally accuracy has been measured.
No model has been chosen or downloaded. The only overlay is manual table geometry.

## Next step

Implement a small app-owned worker-process job mechanism with isolated job state,
progress, cooperative cancellation, a bounded queue, and cleanup before adding
uploads. Follow the retention policy in AGENTS.md: private job directories,
failed/cancelled input deletion, one-hour expiry for review artifacts, startup and
periodic cleanup, and no deletion of active jobs. Never block the HTTP event loop.
Test lifecycle and failure handling before wiring actual video analysis into it.
Then establish a video-appropriate detection/tracking baseline and a small,
manually annotated evaluation subset; keep uncertain contacts/rallies explicit.

## Resume commands

Check branch, working tree, and any existing server before starting a new one.
The last development server was at http://127.0.0.1:8014; it may not survive until
the next session. Port 8000 was occupied by Coach App; do not stop that server.

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8014
```

Continue on develop in small commits. Keep master unchanged.
