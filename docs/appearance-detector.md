# Full-shape appearance detector protocol

Baseline is normal tracking at 0e2fb4c. All inspected labels through 299 are
now development evidence, including ball-validation.json. Before reviewing or
scoring 300–339, freeze a new candidate: connect full bright/contrasting shapes,
then require positive motion on at least max(10 scaled pixels, 15% of shape).
Use area 25–180, extent 24, aspect <=6, fill >=0.45, and median HSV value <=145
in a 4px outer bounding-box ring, all geometric thresholds scaled from 768px.
Brightness/saturation/contrast and temporal association thresholds stay unchanged.
No hue or hardcoded table coordinate identifies a ball. This is an experimental
isolated-bright-object filter on darker backgrounds, not semantic classification.

Development-only initial trials of filtering motion-clipped components failed
on 260–299 (19/37 correct, one wrong), so they were rejected. Full-shape centers
with separate motion evidence produced 24/26, 27/29, 27/28 and 37/37 matches on
the existing visible sequences, with zero wrong associations and zero observations
on 30 negative labels. This is development, not fresh validation.

Reserve 300–339 for source-only manual labels before either algorithm is scored.
Use the same region, video hash, 8px tolerance, uncertain-label policy and full
preceding-frame context. Accept only with no added wrong/negative associations,
no reduction of reserved correct matches, and a net development match gain;
report individual losses and extra candidate costs. No retuning after reserved
results. Export/run the exact baseline commit for comparison. This adjacent
same-video sample cannot establish independent-video generalization or contacts.

## Outcome and normal worker integration

Candidate accepted under the prospective criteria, without changing parameters
after reserved review. Normal TrackingRun and requested worker tracking now use
full_shape_v1. The result identifies its detector version. Candidate coordinates
measure the full bright/contrast component, while motion only validates evidence;
this avoids discarding a slowly displaced ball solely because its moving edge
contains fewer than 35 pixels. The background rule rejects some brighter contexts
and does not identify players, clothing, rackets, or physical ball identity.

| Data | Baseline correct | Full-shape correct | Baseline wrong | Full-shape wrong |
| --- | ---: | ---: | ---: | ---: |
| Development 140–169 (26 visible) | 26 | 24 | 0 | 0 |
| Development 230–259 (29 visible) | 29 | 27 | 0 | 0 |
| Development 195–224 (28 visible) | 8 | 27 | 0 | 0 |
| Development 260–299 (37 visible) | 34 | 37 | 0 | 0 |
| Reserved 300–339 (23 visible) | 19 | 20 | 0 | 0 |

Development totals are 97/120 versus 115/120; four easy-sequence matches were lost.
Extra candidates on visible development labels fell from 64 to 9. The 30 negative
development labels had zero associated observations in either method. On reserved
labels, extra visible-frame candidates fell from 27 to 14. All 16 reserved negative
labels had zero associated observations in either method, although frames with
unassociated candidates increased from three to four. One boundary frame (323)
is uncertain and excluded; missing/negative labels are not inferred rally ends.
The reserved candidate still misses three visible labels. This narrow same-video
result is not proof of robust identity or independent generalization.

Labels were manually read from source-only grids before either reserved score.
Baseline ran from exported commit 0e2fb4c. Final normal and legacy evaluations
match the respective frozen per-frame records and scores exactly. No contact,
rally, camera stabilization, 3D, or physical-speed inference was introduced.

```bash
.venv/bin/python -m evaluation.evaluate_ball_sequences /path/to/clip.mp4 --annotations evaluation/ball-appearance-validation.json
.venv/bin/python -m evaluation.evaluate_ball_sequences /path/to/clip.mp4 --annotations evaluation/ball-appearance-validation.json --legacy-detector
```

The old motion-clipped detector remains available through --legacy-detector for
historical comparisons. The earlier rejected --small-candidate-continuation
always uses that legacy detector and remains offline-only. Historical sparse
held_out labels are development evidence: current tracking matches 6/6, compared
with historical 5/6, with zero observations on three negatives. These are not fresh
validation results and should not be presented as independent accuracy.

88 Python tests passed, including full-center preservation under small motion,
static and bright-surrounding rejection, sparse shapes, source scaling, candidate
overflow, default pipeline confirmation, and worker detector identification.
An actual source-video upload through the ASGI HTTP routes completed in a spawned
worker with 360 source records equal to offline output. Explicit deletion left
zero private job directories and preserved the original file. This validates the
API/worker path; the browser overlay was not re-tested in this increment.

Remaining limits: motionless balls, light backgrounds, watermark overlap, clipped
search boundaries and merged racket/ball appearances can fail. Moving compact
false objects may still pass. Next inspect the lost easy-sequence matches and
whole-video false tracks with separate annotations, then test a distinct fixed-
camera recording before describing general reliability or starting contact rules.
