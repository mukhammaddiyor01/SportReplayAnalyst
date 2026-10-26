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
still apply. UI integration remains a separate increment.
