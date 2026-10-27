# Continue Sports Replay Analyst

Checkpoint: 2026-10-27, tracking loss diagnostics and early initialization review.

## Previous session handoff — resumed 2026-10-27

The prior session was saved for a user-triggered continuation. The user resumed
on 2026-10-27. The following list records the earlier implementation checkpoint.
The last implementation commit is 0a02c0b on develop. Recent completed increments:

- 8fac9da: full_shape_v1 detector, same-video reserved evaluation, worker integration.
- 4c066b0: source-timed missing-observation intervals and browser review navigation.
- 5f39a41: simplified upload, calibration, analysis and review interface.
- 0a02c0b: actual-source frame stepping, keyboard controls, decoder boundary fix.

At checkpoint, implementation changes were committed and the working tree was
clean. Keep develop pushed; master remains 42a6008. Current verification is 94
passing Python tests plus JS syntax and real-video/browser checks documented below.
No contact/rally inference or deployment is complete or authorized by this handoff.

On resume, read this file and AGENTS.md, check Git status before edits, then follow
Next step below. Preserve the clean interface and existing core logic. Do not
interpret a missing observation as a contact, occlusion, or rally end. Browser job
results/copies expire after one hour and are not persistent project memory; reload
the user's source video and rerun tracking when needed. Do not expect today's
browser result to survive until tomorrow. Sources/docs are the durable checkpoint.

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
Track ball (experimental) now runs full_shape_v1 bright-component extraction and pure Python
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

## Difficult/negative follow-up

The same frozen diagnostic now includes 195–224 (28 visible, two uncertain) and
80–109 (30 frames with no ball visually identifiable in the search region).
Difficult frames: 15/28 nearby candidates, 8/28 correct associations, zero wrong
associations, 20 misses. Visible-loss runs are 195–207 and 210–216; association
resumes at 217. All 30 negatives have no candidates/observations. Earlier easy
sequence scores remain unchanged. This is still inspected same-video evidence.

Candidate-area inspection found 25–34px components near the manual ball centers
on 195–207, below the frozen 35px minimum. Multi-candidate initialization blocks
210–214; 215–216 are tentative. No production thresholds or tracker rules changed.
Offline reports now include candidate coverage and per-frame diagnostic details;
candidate lists are not added to worker/API results. 78 Python tests pass.

## Small-candidate experiment: rejected for normal tracking

A fresh protocol was documented before annotating reserved frames 260–299.
Earlier sparse/dense labels, including the historical held_out split, are now
explicitly development evidence. Candidate: keep 35px initialization, admit
25px components only within 0.18s of a confirmed observation. This improved
development from 63/83 to 81/83 correct associations, with two lost easy matches,
zero wrong observations, and unchanged zero/30 negative associations.

Reserved same-video review had 37 visible/three uncertain labels. Audited baseline:
34 correct, zero wrong, three missed. Candidate: 22 correct, two wrong, 13 missed.
Candidate coverage rose 34 to 37 but extra candidates rose 31 to 71. Two coarse
manual centers were corrected after source-only enlarged review; annotations
and docs/tracking-refinement.md disclose original and audited scores. No rules
were retuned after reserved inspection. Candidate was rejected and is disabled
in normal workers/API. Only offline --small-candidate-continuation enables it.

82 tests passed. Final default per-frame records and scores equal the exported
142d5be baseline exactly on the reserved labels. No production quality gain is
claimed. See evaluation/ball-validation.json and docs/tracking-refinement.md.
The newly inspected validation interval is no longer untouched for future tuning.

## Current full-shape detector

Normal worker/API tracking uses full_shape_v1. Connect the full bright/contrast
component, require motion on max(10 scaled pixels, 15% of area), area 25–180,
extent <=24, aspect <=6, fill >=0.45, and median surrounding V<=145 in a 4px
ring, with geometry scaled from 768px. No hue/table-coordinate classifier.
Temporal rules and observation-only rendering are unchanged. Result metadata
identifies the detector. --legacy-detector reproduces the old motion-clipped
baseline; --small-candidate-continuation forces the rejected legacy experiment.

Prospective protocol in docs/appearance-detector.md was frozen before manual
labels/scoring on 300–339. Baseline from exported 0e2fb4c: 19/23 correct, zero
wrong, four missed. Full-shape: 20/23 correct, zero wrong, three missed. Both had
zero observations on 16 negatives; one boundary frame is uncertain. Extra visible
candidates fell 27 to 14, but negative frames with candidates rose three to four.
Development (all older inspected labels) rose 97/120 to 115/120 with four easy
matches lost, zero wrong observations and zero/30 negative associations. Historical
sparse held_out is now development: 6/6 vs 5/6. No independent-video claim.

88 tests passed. Actual source upload through HTTP ASGI routes completed in a
spawned worker: 360 records equal offline output, explicit delete left zero
private job directories, original preserved. Final default and legacy reserved
records/scores equal frozen evaluations. No browser retest this increment.

## Tracking gap review

TrackingRun.result now returns review_gaps from a plain Python service, preserving
source first/last indices/times, frame counts, statuses, boundary classification,
and adjacent track IDs/resume time. No physical duration, contact, occlusion, or
rally is inferred. Dense indices, monotonic times and observation/status consistency
are checked. Frontend renders actual interval buttons that pause/seek to the first
missing frame. Clear result or clip changes clear review. Timestamp fallback or
source/playback dimension mismatch disables navigation. See tracking-review.md.
94 Python tests and JS syntax checks passed. Actual browser tracking returned
360 frames, 227 associations and 11 review intervals (runtime counts, not accuracy).
Clicking 4.972s selected source frame 149 with no observation/marker. Seeking to
6.006s showed frame 180 and cleared the active review indication. Clear result
hid the list. Final browser warn/error logs were empty, screenshot outside Git.
An actual HTTP/ASGI spawned-worker check matched offline 360-frame output;
explicit deletion left zero private job directories and preserved the original.
The final browser result is retained normally for review.

## Clean replay workflow

Frontend workflow now puts Choose video in a toolbar above the player. The wide
layout groups calibration/analysis in the side panel and review below the video;
narrow order is source, video, controls, review. Track ball is the primary action.
Inspection-only and numeric results are in Inspection details. Dynamic phase and
next-action hints reflect actual clip/calibration/job state. Review now pauses,
seeks and scrolls the video into view; one-frame messages use singular text.
No backend/tracking rules changed. Retention/privacy remain visible and expandable.

94 Python tests passed; JS syntax and HTML integrity checks passed. Actual browser
flow verified upload, numeric corners/check, tracking, progress/completion, details
disclosure, review navigation to missing frame 149 and seek to observed frame 180.
The final 544px viewport had no horizontal overflow; browser warn/error logs were
empty. Screenshot is outside Git. See docs/replay-usability.md for scope and limits.

## Source-frame stepping

Previous/Next frame (−1/+1) buttons now use actual tracking frame timestamp
intervals, with no nominal-FPS step. Seeking to the interval midpoint avoids an
observed browser boundary-rounding error. Buttons stay disabled without matching
usable tracking results; clear/result reset disables them again. First/last
records bound stepping. Left/Right arrows work only in playback controls, leaving
native slider/coordinate editing and modifier shortcuts alone. Trail-hidden mode
still identifies the current frame. Narrow playback puts the slider on a new row.

Browser verified 149 → 148 → 149 → 150, 0/359 bounds, 359 → 358 → 359, hidden
trail stepping, both arrow shortcuts, and native slider Right moving only .001s.
Final frame 181 showed an associated marker. Browser warn/error logs empty;
proof outside Git. 94 Python tests and JS syntax passed. No detector/event rule
changed. See docs/replay-usability.md.

## Loss diagnostics and initialization review (2026-10-27)

Added optional component rejection reporting in the appearance detector and an
offline evaluation.diagnose_tracking_losses CLI. Normal workers/API omit those
diagnostics. Source coordinates, first failed filters and null unevaluated metrics
are explicit; nearby boxes are context, not confirmed ball identity. Reports
retain at most 16 nearby components per failure and expose omissions.

Known misses: 142 has a nearby candidate but tentative confirmation. 149, 215,
248 and 249 show large-area/over-extent nearby components; source line/watermark
overlap is a plausible cause, not a proven object classification. The detector's
minimum-area setting is not the cause of these particular failures. No thresholds
or association rules changed. All 360 source records match the pre-refactor snapshot.

New ball-initialization-review.json labels frames 0–29: 25 visible, five uncertain,
19 near-reference associations, zero away, six missing (5–9 and 17). The fixed
search window differs from browser ROI. Four coarse centers were audited after
initial scoring; the annotation metadata and report disclose changes. This is
same-video single-reviewer evidence, not an untouched test or whole-clip validation.
100 Python tests passed. See docs/tracking-loss-diagnostics.md for exact findings.

## Next step

Obtain a distinct fixed-camera recording with the entire table and visible ball
interactions for independent evaluation and eventual contact evidence. Existing
inspected frames support development only. Do not retune against 300–339 as a
holdout. Review other full-video false-track intervals when appropriate; the new
early review only covers 0–29. Keep the clean interface and explicit uncertainty.

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
