# Full-frame ball box evaluation

Stage 2 now has an explicit offline evaluator for reviewed bounding boxes and
full-frame negatives: evaluation.evaluate_box_detector. It does not change the
normal OpenCV worker, train a model or promote a checkpoint.

## Input and provenance

Use existing reviewed YOLO exports produced by evaluation.ball_dataset, with their
provenance.json, images/ and labels/. The existing loader verifies source identity,
image checksums/dimensions and exact YOLO label text against manual review. Only
visible and explicit not_visible frames are scored; uncertain/unreviewed frames
are excluded. Repeated source-SHA/frame-index pairs are rejected across exports.
At most 32 exports, 2000 usable images and 512 MiB are admitted. Source grouping and
prior exposure still need human review; an evaluation run does not establish
recording independence or validate the annotation itself.

Inference consumes the entire prepared image, without the point evaluator's ROI
crop. A prepared Lion image is already a crop of its original portrait source;
source transforms still apply. Keep full-frame negative review explicit: existing
point-only search-region negatives cannot be substituted without full-image review.
The annotation format currently permits at most one ball per image. Do not use
it for scenes with multiple visible balls or partially labeled extra balls.

## Fixed operating point and metrics

- CPU, image size 640, confidence >=0.25, NMS IoU 0.7, max_det 100.
- Single selected ball class, default 0; class 32 is available for verified COCO weights.
- Match a predicted source-image xyxy box to the manual visible extent at IoU >=0.5.
  In confidence order, at most one prediction can match the one reference box.
  All other selected predictions, including duplicate matches, are false positives.
- An unmatched visible reference is a false negative. Every selected prediction on
  an explicit negative image is a false positive. Report negative frames containing
  predictions separately from total false-positive box count.
- Precision = TP/(TP+FP); recall = TP/(TP+FN). A zero denominator produces null,
  never a fabricated perfect value. Report counts and per-recording totals.
- Frames returning 100 detections are marked detection_limit_reached. This signals
  possible saturation; it does not establish how many detections were suppressed.
  False-positive counts can therefore be lower bounds when the cap is reached.

These are metrics at one operating point, not an AP/mAP curve, temporal tracking,
physical identity or independent-video accuracy. Box extent/blur uncertainty matters
at IoU 0.5; independent review remains necessary. Do not compare these results
numerically with earlier 8px center/ROI scores as though they were the same task.
Any baseline comparison must freeze the same input region and metric definitions.

## Local command

Use the separate environment from requirements-yolo.txt, not the normal app env.
Provide existing local weights and their pinned SHA256; no startup downloads.
Socket connections are blocked while loading/inferencing; sync is disabled.
The command prints a JSON report. Save it outside Git if needed.

```bash
python -m evaluation.evaluate_box_detector --exports /path/to/reviewed-export /path/to/another-reviewed-export --model /path/to/best.pt --model-sha256 CHECKPOINT_SHA256 --ball-class 0
```

The report records checkpoint/export hashes, settings, source indices/dimensions,
timestamp provenance, per-frame counts, overall totals and recording totals. It
contains no images or personal source paths. Local prepared images and weights
remain outside Git and are not governed by temporary analysis-job expiry.

## Verification (2026-10-29)

Eight new automated tests cover IoU/duplicate matching, center-only false matches,
misses, explicit negatives, class/confidence filtering, zero denominators, invalid
geometry, altered exports, duplicate source frames, model checksum rejection and
full-frame inference composition with a synthetic framework stub. The stub verifies
socket blocking and orchestration; it is not real inference or model quality evidence.
The full suite passes 139 tests without torch or model downloads.

The real four reviewed exports were revalidated: 31 usable frames, comprising
25 visible boxes (Getty 18, Lion 7) and 6 Getty full-frame negatives. Five uncertain
labels remain excluded. No labels changed. The temporary optional ML environment
from the earlier smoke run is no longer present; no real model inference or new
training was performed during this checkpoint. Recreate the pinned isolated env
before using this evaluator with the preserved local checkpoint. No detector or
tracking improvement, fresh validation or stage completion is claimed.
