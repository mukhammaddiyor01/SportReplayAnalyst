# Sports Replay Analyst — Development Rules

## Goal and Current Stage

Build a local application for analyzing prerecorded table tennis video: ball
observations and image-space tracks, estimated table contacts, and rally timing.
The minimal application setup and bounded local video reader are implemented.
The current stage adds manual table calibration and verifies coordinate handling.
Do not claim that tracking or event detection already works. Implement subsequent
work in small, independently verified steps. Do not modify reference projects.
Conversation is in Uzbek; code, interface, comments, and documentation are English.

## Scope and Technology

Start with one prerecorded video, one stationary camera, and the whole playing
surface visible. Allow manual selection of the four table corners.
Use Python 3.12, OpenCV, NumPy, FastAPI, Jinja2, and plain HTML/CSS/JavaScript.
No database, live camera, multiple cameras, player identification, shot
classification, automatic scoring, or deployment in the first version.
Use the installed frontend-design skill when implementing the interface.
Prioritize video, overlays, timeline, and clear controls. Never fabricate statistics.

## Responsibilities and Readability

- `backend/main.py`: application composition and intended public mounts.
- `backend/routes.py`: request validation and workflow coordination.
- `backend/adapters/`: video decoding, OpenCV, inference, and library operations.
- `backend/services/`: plain Python tracking, event, and rally rules, independent
  of FastAPI, OpenCV, inference frameworks, and HTTP.
- `backend/config.py`: named limits and experimental thresholds.
- `frontend/templates/` and `frontend/static/`: views and browser behavior.
- `tests/` and `docs/`: meaningful checks and stage-specific documentation.

Create files only when needed. Avoid abstract classes, repository layers,
dependency injection containers, and speculative architecture.
Use descriptive names, small functions, guard clauses, and readable formatting.
Translate expected service errors in controllers. Do not hide failures or expose
tracebacks. Do not use assertions for runtime input validation.
Keep each video's tracking state isolated; never use shared global user counters.

## Video Geometry and Time

Keep decoded frame indices, source dimensions, and timestamps with observations.
Prefer valid presentation timestamps; explicitly document FPS-based fallbacks.
Record frame gaps and variable-rate limitations. Never silently renumber sampled
frames or treat a missing observation as a measured ball position.
Maintain explicit source-to-preview coordinate transforms when resizing or
letterboxing. Store table corners in source coordinates and validate their order,
convexity, area, and bounds before computing a homography.
Image-space tracks are not 3D trajectories. Projecting an airborne ball through
a table-plane homography does not produce its true table coordinates.
Only estimate a contact location under documented plane/calibration assumptions.
Detect camera movement or calibration drift and invalidate or request calibration
again; do not silently continue using stale corners.

## Detection, Tracking, Events, and Rallies

Inspect real footage before selecting a detector. Do not assume a general-purpose
object detector resolves a small, fast, blurred table tennis ball. Evaluate any
chosen model on the actual conditions before describing it as suitable.
Keep observations, predictions, missing states, and uncertainty distinguishable.
Use bounded motion association and short-gap recovery; reject implausible
candidates. Do not draw interpolated positions as measured evidence.
A change in 2D direction alone is insufficient evidence of a table contact.
Distinguish racket interactions, plausible table contacts, and tracking errors
using temporal continuity, table/racket context where observable, and independent
contact evidence. If that evidence is unavailable, return an uncertain candidate
or no decision. Do not force classification from a top-down trajectory.
Deduplicate event candidates over time and document the experimental rules.
Before implementing rally timing, document start confirmation, tolerated tracking
gaps in seconds, termination evidence, reset behavior, and video-boundary truncation.
A single lost frame must not end a rally. Detection absence and a confirmed
rally end are different states. Report timing uncertainty when evidence is weak.
Do not invent confidence percentages, accuracy figures, speeds, or physical units.

## Local Processing, Limits, and Cleanup

Process videos locally; never send them to hosted AI services.
Before adding uploads, implement and document this initial bounded policy:
maximum 100 MiB, 60 seconds, 1920x1080, and 120 FPS. Validate decoded dimensions,
duration, timestamps, and actual frame count as well as container metadata.
Reject unsupported media and stop processing if runtime limits are exceeded.
Read uploads with a streaming byte limit into a private, randomly named job
directory outside public assets. Never use client filenames as filesystem paths.
Keep one active analysis job per local app instance with a bounded queue; report
busy explicitly. Use an app-owned worker process for long analysis, with progress
and cooperative cancellation checked between frames. Keep the HTTP event loop
free and avoid implying restart durability. Shut down workers cleanly.
Delete partial inputs on rejection, error, or cancellation. Keep completed inputs
and results only for the active review session, expiring after one hour; provide
explicit deletion and sweep expired leftovers at startup and periodically.
Prevent deleting a running job's files. Document crash cleanup and retention in
the interface before accepting uploads. Keep job state isolated and access scoped.
Bind the local server to `127.0.0.1`. Serve only intended public assets and
explicit, validated job media routes; never mount the repository or job root.
Keep debug responses off. Use local frontend assets and restrict unexpected hosts
and cross-origin mutations. Do not introduce external scripts, fonts, or analytics.
Never commit videos, frames, model weights, secrets, .env files, virtual
environments, logs, caches, temporary inputs, or generated analysis output.
Ignore these before adding application data. Model downloads must be explicit,
pinned, integrity checked, and licensed; do not download weights at startup.

## Initial Footage and Verification

The user supplied a Getty Images preview MP4. Local OpenCV metadata inspection
reported 360 frames, 768x432, approximately 29.970 FPS, and 12.012 seconds.
Sampled frames show an overhead view, visible playing surface, a watermark,
blurred ball appearances, and apparent table movement between samples.
This is a candidate for initial video/track experiments, not validated contact
or rally ground truth. Check all frames, camera stability, and decodability before
accepting it as a stationary-camera evaluation clip. Do not publish the footage
or derived frames in Git. Request a more suitable fixed-camera clip if needed.

Use unittest for plain Python rules and appropriate HTTP/adapter checks.
Cover tracking association, short occlusions, false detections, duplicate events,
rally boundaries, cancellation, cleanup, invalid media, and coordinate/time
consistency as those features arrive. Keep automated checks independent of model
downloads, internet access, and a GPU.
Create a small manually annotated subset of real footage; separate tuning and
held-out evaluation segments. Evaluate detection/tracking, contacts, and rally
timing separately. Label ambiguous events instead of inventing ground truth.
Report only tests and real-video evaluations actually performed.

## Milestones and Git

1. Commit AGENTS.md before any application code.
2. Create and verify the minimal application setup, privacy ignores, and README.
3. Verify bounded video reading, real timestamps, and manual table calibration.
4. Add isolated background jobs, progress, cancellation, and cleanup before uploads.
5. Establish and evaluate ball detection and tracking on the real clip.
6. Add event candidates and explicit rally rules only after their evidence is defined.
7. Connect real results to video overlays and timeline; evaluate limitations.

Use only `feat:` and `fix:` commit prefixes. Verify and commit every small,
complete logical change before starting the next. Review exact staged changes
and stage only relevant files. Do not commit personal filesystem paths or secrets.
The user authorized pushes after checking the supplied GitHub repository.
The initial setup, including these preceding rules, belongs on both `master`
and `develop`. Keep `master` at the completed initial setup; subsequent
implementation commits and pushes belong only on `develop`. Do not advance
`master` afterward without a separate explicit instruction. Never force push.
Deployment is outside the authorized scope.
