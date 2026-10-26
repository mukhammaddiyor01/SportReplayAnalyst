# Experimental temporal ball association

## Pure Python rules

BallTracker consumes bounded candidate batches and original source frame indices
and timestamps. It does not import OpenCV, NumPy, HTTP, or inference frameworks.
Each video owns its own tracker; no shared global tracking state exists.

Initialization requires three consecutive unique, temporally coherent candidates
with net image displacement above 0.8% of the source diagonal. Static fragments
and isolated detections do not become an observed track. Persistent moving false
objects can still satisfy these rules; association is not proof of ball identity.

Once initialized, constant image-velocity prediction gates candidates by residual
distance and maximum source-time-based displacement. Gates and ambiguity margins
scale with the image diagonal. They are experimental image parameters, not
physical ball speeds or confidence probabilities. Component size never chooses
the winner. Close competing candidates and truncated batches remain ambiguous.

A gap up to 0.18 seconds may retain track identity; the output contains a separate
prediction, never a measured observation. Longer gaps expire identity and require
new confirmation. Source-index discontinuities and recovered detections mark
break_before so renderers must not draw a solid line across missing evidence.

The statuses are searching, tentative, observed, predicted, and ambiguous. Only
observed carries an associated measured candidate. Prediction fields are separate;
out-of-image predictions are omitted. Newly confirmed tracks do not retroactively
turn earlier tentative frames into observations. IDs are local to one video.

The service validates monotonic source time/index and finite source coordinates
before mutating state. Explicit reset clears all video state.

## Initial verification

Thirteen service checks cover confirmation, static false objects, a distant
competing object, nearby ambiguity, candidate overflow, short-gap recovery,
long-gap identity reset, skipped frame indices, impossible jumps, irregular
source intervals, invalid input, reset/isolation, and interrupted initialization.
These tests establish rule behavior; real-video association evaluation is a
separate next increment. They do not establish tracking accuracy on real footage.

Contacts, racket strikes, rallies, 3D geometry, and physical speed are not inferred.
Camera drift is not compensated; any future trail is in raw image coordinates.

## Sequential real-video evaluation and worker integration

TrackingRun now feeds every decoded source frame through candidate extraction and
association. Records preserve original frame index, timestamp/source, candidate
count, separate observation/prediction fields, local track ID, and trail breaks.
The existing worker can optionally return these bounded records. Raw image pixels
are not included in the HTTP result. Uploaded copies and records use the existing
private storage, cancellation, runtime, expiry, and cleanup mechanisms.

POST /api/inspections accepts optional mode=track plus an explicit search_region
image rectangle. Missing/invalid options are rejected before reserving a slot.
The worker rechecks the window against actual decoded dimensions. Inspection
without tracking remains the default. No table-plane transform is applied.

70 automated checks passed at this increment, including pure tracking rules,
real CV-to-service composition, source record separation, independent runs,
worker serialization, request validation, and invalid-window cleanup.

The initial association parameters were evaluated without adjusting against
held-out failures. Existing sparse pilot results were:

| Split | Visible reference labels | Associated observation near reference | Associated observation elsewhere | No observation | Negative labels with an observation |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tuning | 6 | 6 | 0 | 0 | 0 of 3 |
| Held out | 6 | 5 | 0 | 1 | 0 of 3 |

Frame 210 remained ambiguous during reinitialization near the player. Its
prediction was not counted as an observation or silently substituted. Frames
183/186 associated the ball-like candidate instead of the distant clothing
candidate. Later labels used a new local track ID after loss/reinitialization.
Those IDs are not rally counts or proof of persistent ball identity.

```bash
.venv/bin/python -m evaluation.evaluate_ball_tracking /path/to/clip.mp4 --split held_out
```

The evaluator processes unlabeled earlier frames as inference context, including
past frames in the candidate-tuning segment. Labels are used only for scoring;
there is no learned model. This reuses the small same-video pilot and does not
measure dense temporal identity, identity switches, real occlusion recovery,
full-flight correctness, or generalization. Additional sequence annotations are
required. The underlying detector's small-ball and clothing-fragment failures
still apply. The browser integration described below was verified in the following increment.

## Browser 2D overlay

After four corners are checked, the browser derives a padded rectangle (2% of
source width/height on each side, clipped to the image). This is only a coarse
search window. Track ball explicitly requests tracking; Inspect video still
runs without it. Neither applies the table-plane homography to airborne points.
The browser-derived window differs slightly from the fixed pilot window; browser
record totals are not substituted for the offline pilot scores.

The tracking canvas matches source video dimensions. Playback uses presented
video media timestamps when available; seeking uses timestamp lookup. A 0.6s tail
contains only observed records with the same track ID. Missing/ambiguous frames,
source-index gaps, and break_before markers interrupt the line. The current marker
appears only on observed records. Tentative/predicted locations are not plotted.
Estimated timestamps or playback/source size mismatches disable the overlay.

Actual browser checks on the supplied clip verified:

- Frame 180 at 6.006s showed a candidate marker and image-space trail aligned
  with the visible ball. Playback advanced the displayed source frame.
- Frame 210 at 7.007s showed no observation (ambiguous), without a false marker.
- The overlay checkbox hid/restored the trail.
- Clear result removed the overlay/records and left zero private job directories.
- Cancelling an actual tracking job stopped its worker and left zero private
  job directories; the original source file remained present.
- Final tracking completion returned 360 source records, including 208 associated
  observations and 20 prediction-only frames for this browser search window.
  These are processing counts, not verified ball accuracy or rally statistics.

The final flow's browser error/warning logs were empty. JavaScript syntax checks
passed. Screenshots remain outside Git because they contain user-provided footage.
70 Python checks passed, including the worker-mode/region validation and cleanup.

Next, expand manually labeled sequences and review false tracks/losses before
contact or rally inference. Synthetic short-gap tests are not proof of reliable
recovery through real occlusions. No stabilization or 3D inference was added.

## Dense sequence diagnostic (2026-10-26)

Numeric manual annotations in evaluation/ball-sequences.json now cover every
frame of 140–169 and 230–259. Centers are approximate visible blur midpoints,
read from native source crops with a coordinate grid before running the sequence
scores. No points were interpolated or copied from detector output. Five frames
near racket/player interactions could not be confidently labeled and remain
uncertain; they are not counted as negatives or assumed occlusions. Labels have
one reviewer and no expert review. The matching radius stays 8 source pixels.

The baseline parameters and search window stayed frozen. Frames 140–169 overlap
the previous tuning segment. Frames 230–259 are an additional same-video review,
not an independent held-out benchmark. All preceding frames are processed as
unlabeled inference context. This annotation set does not test false tracks when
the ball is absent, or establish whole-video accuracy.

| Sequence | Visible | Near manual center | Wrong | Missed | Uncertain | Correct runs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Tuning 140–169 | 26 | 26 | 0 | 0 | 4 | 2 |
| Review 230–259 | 29 | 29 | 0 | 0 | 1 | 2 |

Correct runs break at uncertain/missing/wrong observations, explicit trail breaks,
or changed IDs. Changes between correct IDs are counted only within continuously
visible labeled intervals, including intervening visible losses. Both sequences
had zero such changes and zero labeled visible-loss frames. These diagnostic
counts are not standard MOT identity metrics, confirmed occlusion recovery, or
rally boundaries. Each loss report includes first/last source time and frame count;
its endpoint span is not an inferred physical occlusion duration.

```bash
.venv/bin/python -m evaluation.evaluate_ball_sequences /path/to/clip.mp4
```

The evaluator rejects incomplete/nonconsecutive sequences and scores observations
only. Predictions cannot earn a match. Six new automated checks cover visible
losses, wrong points, identity changes across losses, uncertain/negative handling,
trail boundaries, and invalid labels. All 76 Python tests passed. The original
sparse held-out evaluation still returns 5/6 matches, one withheld ambiguous
frame (210), and zero observations on its three negatives. No detector/tracker
threshold was changed to improve these scores.

Next evaluate a dense difficult interval around the known ambiguity at 210 and
ball-absent intervals to measure false initializations. Keep those diagnostic
labels separate from any future tuning protocol. Contact/rally work still waits
for independent evidence and explicit event rules.

## Difficult and negative sequence review (2026-10-26)

The frozen diagnostic set now also covers 195–224 and 80–109. Manual source
review labeled 28 visible centers and two uncertain racket-adjacent frames in
195–224. The latter are excluded, not invented occlusion/contact truth. No ball
was visually identifiable in the search region in 80–109. These negative labels
say nothing about physical absence outside the region or behind a player.
Both intervals overlap previously inspected sparse labels; neither is a new
holdout. No detector or tracker parameter was changed.

The offline evaluator now distinguishes a missing nearby candidate from a
nearby candidate without a correct association. It reports per-frame source
time, status, manual center, observation, candidate count, and nearby-candidate
presence so failures can be located in the original video. TrackingRun returns
its candidate batch to an offline caller; production worker records and API
payloads still omit candidate lists. Missing diagnostics are not counted as
negative detection evidence. Uncertain labels are excluded from detection scores.

| Diagnostic | Visible | Nearby candidate | Correct association | Wrong association | Missed association | Uncertain |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Difficult 195–224 | 28 | 15 | 8 | 0 | 20 | 2 |

The 30 negative frames had zero candidate batches containing a candidate and
zero associated observations. This tests one quiet interval, not the entire clip
or all clothing false positives. The two easier intervals retain their previous
26/26 and 29/29 matches. The difficult interval contains two visible-loss runs:
195–207 (13 frames, source endpoints 6.5065–6.9069s) and 210–216 (seven frames,
7.0070–7.2072s). Correct tracking resumes at 217. Unknown frames 208–209 interrupt
label evidence, so the evaluator does not merge losses across them or infer
physical occlusion length. Zero identity changes in the scored interval does not
prove identity preservation: no earlier correct association exists in this window.

A separate inspection of the pre-area-filter connected components near manual
centers found areas of 25–34 pixels on frames 195–207, below the frozen minimum
of 35. This identifies an area-filter failure on those frames. Frames 210–214
contain nearby candidates but multiple candidates prevent unique initialization;
215–216 are tentative before confirmation at 217. Predictions remain unscored.
These are two distinct bottlenecks, not evidence of a contact or rally boundary.

All 78 automated Python checks passed. New scoring checks separate detector and
association losses and distinguish negative candidates from confirmed false
tracks. The adapter check verifies candidate batches can be inspected without
adding them to production result records. User footage and generated diagnostic
results remain outside Git; only numeric manual annotations are committed.

Before changing thresholds, define a new development/holdout protocol: these
already-inspected intervals can support development, but cannot remain an
untouched test. A lower area threshold may improve small-ball coverage while
reintroducing clothing fragments; compare both detection and tracking against
the frozen baseline on newly annotated, uninspected footage/segments. A separate
fixed-camera clip is still needed to assess generalization and contact evidence.
