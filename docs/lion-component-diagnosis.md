# Lion component-loss diagnosis (2026-10-27)

This follows the frozen sparse-motion comparison; the inspected labels are now
development evidence. No detector/tracker threshold, ROI or manual label changed.
The diagnostic CLI now accepts `--sparse-motion` so component extraction and
association use the same experiment mode; its default remains full_shape_v1.
Source hashes, crop transform and fixed ROI are in lion-footage-review.md and
evaluation/lion-{development,validation}.json. Raw reports remain outside Git.

## Measurements

For each failed visible association, first check for a retained candidate within
8px of the manual center. If none exists, describe the nearby component with the
nearest centroid. This is a descriptive grouping, not proof that the component
is the ball. Multiple nearby fragments can fail at different stages. The first
failed gate only is measured; later checks are not inferred.

| Interval / mode | Failed associations | Candidate present | Nearest component: area | fill | motion | background |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 20–49 baseline | 30 | 0 | 4 | 5 | 12 | 9 |
| 20–49 sparse candidate | 27 | 6 | 4 | 5 | 12 | 0 |
| 60–89 baseline (12 visible) | 12 | 0 | 5 | 4 | 2 | 1 |
| 60–89 sparse candidate | 12 | 1 | 5 | 4 | 2 | 0 |

Three development associations are correct in the sparse candidate and are not
included in its failure rows. Its six candidate-present misses are frames
20,29,34,36,39,41; confirmation is still withheld. Twelve development motion
failures have zero positively changed pixels inside the selected component,
although the whole adjacent decoded images are not identical. Do not label these
as physical occlusion or delete/renumber their source frames.

Reserved review examples: frames63/64 have nearby sparse mask pieces with fill
.125/.128; frames68/69 have fill .194. Frames65,66/67,70/71 have selected
nearby fragments with areas5,13,8 reference-image pixels respectively. This
supports examining motion-blurred appearance and fragmented masks, rather than
only relaxing temporal confirmation. Background rescue recovers one reserved
candidate (72), but cannot create three consistent observations there.

Reproduce for each annotation file, with/without the final option:

```bash
.venv/bin/python -m evaluation.diagnose_tracking_losses /path/to/lion-table-first-180.mov --annotations evaluation/lion-validation.json --sparse-motion
```

110 Python tests passed, including matched diagnostic/execution mode checks.
The runtime worker and interface are unchanged. No YOLO model has been evaluated
at this diagnosis checkpoint. Establish another reserved interval before any new
detector tuning; keep source-frame/time provenance and uncertain labels explicit.
