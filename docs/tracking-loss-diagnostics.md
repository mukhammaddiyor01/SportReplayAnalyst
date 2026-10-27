# Tracking loss diagnostics

This increment adds offline evidence about full_shape_v1 filtering without changing
thresholds, masks, temporal rules, or browser behavior. find_appearance_candidates
can optionally report each component's source box/center, area, fill, evaluated
moving-pixel count, evaluated surrounding brightness, and first failed filter.
Normal workers do not request diagnostics; no diagnostic arrays are added to API
results. A null rejection means the component passed filters, not guaranteed
retention after candidate overflow. Unevaluated later metrics remain null.

The offline CLI scores visible manual references, then inspects only failed
associations (missing or outside the matching radius). It reports accepted nearby
candidates separately from nearby component boxes. Reports keep at most 16 spatial
component records per failed frame and state how many were omitted. Spatial
proximity does not prove a component is the ball. An absent nearby component can
also mean brightness, saturation, or contrast masking failed. Source identity and
dimensions are checked through the existing collector; early EOF is explicit.

```bash
.venv/bin/python -m evaluation.diagnose_tracking_losses /path/to/clip.mp4
.venv/bin/python -m evaluation.diagnose_tracking_losses /path/to/clip.mp4 --annotations evaluation/ball-initialization-review.json
```

## Existing sequence findings

| Frame | Association state | Accepted nearby candidates | Nearby first-rejection evidence |
| --- | --- | ---: | --- |
| 142 | Tentative | 1 | A candidate passed; confirmation is incomplete |
| 149 | Predicted | 0 | Large-area and over-extent components |
| 215 | Predicted | 0 | Large-area and over-extent components |
| 248 | Predicted | 0 | Large-area and over-extent components |
| 249 | Predicted | 0 | Large-area and over-extent components |

Source review shows overlap with thin table/net lines or watermark text in these
regions. Merged bright shapes are a plausible explanation for enlarged components;
the report does not establish object identity or a contact event. Lowering the
minimum area would not address these particular extent/large-component failures.
No thresholds were adjusted against these already inspected labels.

## Early initialization review

A new numeric annotation set covers frames 0–29 at the fixed offline search window.
Source-only native pixel grids were used without detector overlays/interpolation.
Five player/racket-adjacent frames (0–4) remain uncertain. Of 25 visible references,
19 have an associated observation within 8px, six have no observation, and zero
have an observed point away from reference. Frames 5–9 have nearby accepted
candidates but confirmation is interrupted by ambiguity at 7; frame 17 is missing
with area/extent rejection evidence. No wrong association was found among these
19 scored early observations; the entire clip and all uncertain frames are not
thereby validated. This fixed offline window differs from the browser-derived
window, explaining a different first-confirmation frame.

Initial coarse centers at 26–29 were audited after the first score using enlarged
source-only grids. The annotation file discloses corrections and initial totals
(17 correct, two away, six missed). No algorithm changed during the audit. Labels
are approximate, single-reviewer, same-video diagnostics, not an untouched holdout
or independent expert truth. No whole-video accuracy claim follows.

All 100 Python tests passed. New checks cover passive diagnostics leaving candidate
outputs unchanged, motion/background/area/fill rejection, bounded noisy reports,
and explicit early EOF. All 360 source records (including observations, statuses,
IDs, predictions and timing) exactly match the snapshot before this refactor.
User frames, full reports, and video remain outside Git; only numeric manual labels
and code/docs are committed. No browser change or new browser check this increment.

Next use a distinct fixed-camera clip with the full table and visible ball/table
interaction for independent evaluation. The existing inspected labels support
development, not fresh validation. Further tuning against this one preview alone
would not establish generalization. Contacts/rallies still need independent evidence
and explicit rules; a trajectory reversal or missing point is insufficient.
