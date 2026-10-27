# Sparse-motion candidate protocol (2026-10-27)

Baseline: 06da55f, full_shape_v1 plus three consecutive unique candidate frames.
Second source: the existing 180-frame cropped Lion MOV, SHA256 recorded in
lion-footage-review.md. Use the fixed browser-derived window [161,326,563,517)
and the existing 8px matching tolerance. The broader ROI experiment admitted
player-hand tracks and is not the selected search window.

Development exploration is restricted to Lion frames 0–59 and previously inspected
old-source annotations. The simple single-seed .05s gap allowance falsely followed
a hand and was rejected. Freeze the following candidate before dense review or
scoring of reserved Lion frames 60–89:

- Preserve full_shape_v1 gates; additionally accept bright surroundings only when
  median component V minus median surrounding-ring V is at least 60.
- Keep at most 64 temporal candidate paths, retaining an unmatched path up to .05s
  from its last actual candidate. Saturated/overflow hypotheses reset to ambiguous.
- Require three actual candidates, existing speed/velocity-consistency gates and
  net displacement; confirm only exactly one complete moving path. Multiple viable
  paths remain ambiguous. Missing/tentative points are never backfilled as observed.
- Active-track association/gap rules remain unchanged. Reset clears hypotheses.

Development labels (20–49) are manual source-grid reviews after exploratory output
was seen; they are not blind. Reserved labels (60–89) must be read from source-only
frames before either frozen method is scored. Old data are regression evidence,
not untouched validation. Do not retune to the reserved result. Acceptance requires
no added wrong/negative associations in scored data, a Lion development gain, no
reserved coverage regression, and at most one lost match on old visible labels.
Report sparse coverage and all individual losses even if these criteria pass.
Both methods must see the same complete preceding frames. No general ball-identity,
contact/rally or independent-video accuracy claim follows from this small test.

## Frozen comparison result and decision

The numerical gates passed their narrow acceptance criteria. Nevertheless, the
candidate is **not promoted**: reserved visible coverage remains zero, and the
small development gain does not establish usable tracking on this source.
Normal browser/worker tracking remains full_shape_v1 with consecutive confirmation.
The new method is available offline only with `--sparse-motion`.

| Source / labeled interval | Visible | Baseline correct | Candidate correct | Wrong (both) |
| --- | ---: | ---: | ---: | ---: |
| Lion development 20–49 | 30 | 0 | 3 | 0 |
| Lion reserved 60–89 | 12 | 0 | 0 | 0 |
| Getty 140–169 | 26 | 24 | 24 | 0 |
| Getty 230–259 | 29 | 27 | 27 | 0 |
| Getty 195–224 | 28 | 27 | 27 | 0 |
| Getty 260–299 | 37 | 37 | 37 | 0 |
| Getty 300–339 | 23 | 20 | 20 | 0 |
| Getty 0–29 | 25 | 19 | 18 | 0 |

Lion development confirmations are frames 22, 44 and 48. All other 27 visible
frames are missed. These are three separated runs with one ID change between
correct observations; this is sparse association, not a recovered continuous path.
In reserved frames, all 12 visible labels (63–74) are missed; 18 uncertain labels
are excluded. There are no Lion negative labels, so no Lion false-positive-rate
claim is possible. The candidate detector has a near-reference component on 9/30
development visible frames and only 1/12 reserved visible frames. Association
relaxation alone cannot repair those missing candidate measurements.

Getty loses exactly one prior match, frame 10, due to competing temporal histories.
Its other visible misses are unchanged. Across the 46 labeled Getty negatives,
both methods make zero observed associations. All Getty labels are reused
regression evidence. No whole-prefix false-track audit or fresh-video identity
benchmark was performed. Frames after 89 remain unscored; do not reuse 60–89 as
an untouched validation set after this comparison.

Reproduce each method with the same source and preceding-frame context:

```bash
.venv/bin/python -m evaluation.evaluate_ball_sequences /path/to/lion-table-first-180.mov --annotations evaluation/lion-development.json
.venv/bin/python -m evaluation.evaluate_ball_sequences /path/to/lion-table-first-180.mov --annotations evaluation/lion-development.json --sparse-motion
```

Replace the annotation filename with `lion-validation.json` for the frozen
reserved comparison. Source hashes/dimensions are verified before scoring.
108 Python tests passed, including sparse missing-frame confirmation, competing
paths, stationary distractors, hypothesis overflow, reset/expiry, and relative
background filtering. Existing default worker/API tests also passed. No frontend
changes or browser success claim are part of this offline experiment.

Next: inspect first-failed component stages on the now-development Lion labels,
particularly elongated motion blur and near-repeat appearances. Establish another
reserved interval before any further detector adjustment. Keep the search window
explicit; a wider window already produced hand tracks. Do not proceed to contacts
or rallies while ball evidence remains this sparse.
