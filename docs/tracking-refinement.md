# Small-candidate continuation protocol

Protocol established before labeling/scoring the reserved 260–299 source interval.
Baseline: commit 142d5be, fixed 35px minimum connected-component area at 768px
reference width. All previously inspected sparse/dense labels are now development
material, including the historical held_out split; that filename is historical,
not an untouched test for this refinement. Source identity/window/tolerance stay
as recorded in ball-sequences.json. This remains same-video validation, not
independent generalization or a contact/rally benchmark.

Development-only trials compared a universal 25px minimum and a 25px minimum
only while a confirmed observation is at most 0.18s old. Universal lowering
reduced matches in 140–169 from 26 to 7 by admitting distractors during
initialization, so it was rejected. A strict-first fallback also produced a wrong
association and was rejected. The selected candidate uses 25px only for recent
confirmed tracks, otherwise 35px. It preserves ambiguity, speed, gap and
confirmation rules; no tentative/predicted point becomes an observation.

Before reserved-interval review, freeze this single change: continuation area 25,
initialization area 35, existing 0.18s expiry. Development acceptance requires a
net correct-association gain with no added wrong or negative associations;
individual losses and extra candidates must be reported. Reserved acceptance
requires no added wrong/negative associations and no reduction in total correct
matches versus baseline. Do not retune after reviewing reserved scores; a failure
means reject/defer the candidate and define another untouched test for later work.

Manually label every frame 260–299 from source crops without detector overlays
before scoring either method. Use visible blur midpoints, uncertain labels when
indistinguishable, and negative labels only when no ball is visually identifiable
inside the search window. Keep the same 8px tolerance and full preceding-frame
inference context for both methods. Run baseline from commit 142d5be, not a
reimplemented approximation. Keep video, frames and generated results outside Git.

## Measured outcome: rejected for normal tracking

The frozen recent-track candidate improved development matches from 63/83 to
81/83: 140–169 fell from 26 to 24, 230–259 stayed 29, and 195–224 rose from 8 to
28. Both methods had zero wrong visible associations and zero observations on
30 negative labels. Extra candidates on visible development frames rose from
33 to 81. This met the predefined development criterion but exposed a distractor
cost; it was not sufficient to accept the change.

Reserved 260–299 labels contain 37 visible and three uncertain frames. Initial
coarse labels produced baseline 32 correct/two wrong/three missed and candidate
22 correct/two wrong/13 missed. Enlarged source-only grid review found two manual
center errors at 268 and 274. Corrections are recorded in ball-validation.json;
no algorithm parameter changed after reserved review. These are single-reviewer
approximate labels with a post-score audit, not independently validated truth.

Audited reserved results:

| Method | Visible | Nearby candidate | Correct association | Wrong association | Missed | Extra candidates on visible frames |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline 142d5be | 37 | 34 | 34 | 0 | 3 | 31 |
| Recent-track small candidates | 37 | 37 | 22 | 2 | 13 | 71 |

The candidate incorrectly associates at 269 and 294 and introduces losses around
racket interactions. The interval contains no negative labels; only the earlier
30 development negatives were tested. More nearby candidates do not imply better
tracking: admitting distractors changes velocity/state and later associations.
The candidate fails both reserved acceptance conditions, so it stays disabled.
No threshold or association rule was retuned against these results. The reserved
interval is now inspected evidence and cannot be reused as an untouched future test.

Normal worker/API tracking keeps the 35px minimum. The offline-only flag below
reproduces the rejected candidate. The HTTP schema exposes no such option.

```bash
.venv/bin/python -m evaluation.evaluate_ball_sequences /path/to/clip.mp4 --annotations evaluation/ball-validation.json
.venv/bin/python -m evaluation.evaluate_ball_sequences /path/to/clip.mp4 --annotations evaluation/ball-validation.json --small-candidate-continuation
```

Baseline was run from an exported 142d5be checkout with the same video and labels.
The final default evaluator's per-frame records and all scores equal that exact
baseline. The optional experiment equals the frozen candidate before gating it
off. All 82 Python tests pass, covering scaled small-candidate extraction,
confirmation-only continuation, expiry, ambiguity, and unchanged default behavior.
No production tracking-quality improvement is claimed by this increment.

Next investigate temporal/appearance evidence that distinguishes ball blobs from
player/racket fragments before relaxing detection. Keep association uncertainty
explicit. Use a new reserved interval or separate fixed-camera clip for the next
candidate; avoid cycling thresholds against the now-inspected 260–299 labels.
