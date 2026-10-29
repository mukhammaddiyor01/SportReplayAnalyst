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

## Real checkpoint evaluation (2026-10-29, after environment restoration)

A separate Python 3.12.14 environment was recreated from requirements-yolo.txt:
Ultralytics 8.4.190, torch 2.14.1, torchvision 0.29.1, NumPy 2.5.4 and
opencv-python 4.13.0.92. pip check found no broken requirements. The application
environment still has neither torch nor Ultralytics. All resolved package versions
were recorded locally; transitive dependencies are not fully pinned by the five
versions in requirements-yolo.txt.

The existing smoke best.pt was verified against SHA256
3d0809efe1419a41de8b035e5098371e1066966f9ed7759a8c64d600a186e6cd.
Before inference, the four export-provenance hashes and fixed settings above were
saved in a local protocol receipt. The model then processed all 31 full prepared
images on CPU with sockets blocked and sync disabled. No new model was downloaded,
no labels changed, no training occurred and no threshold sweep followed the result.

| Recording | Visible boxes | Negative images | TP | FP | FN | Negative images with predictions | Detection-limit images |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Getty | 18 | 6 | 0 | 45 | 18 | 6 | 0 |
| Lion | 7 | 0 | 0 | 36 | 7 | 0 | 0 |
| Total | 25 | 6 | 0 | 81 | 25 | 6 | 0 |

Precision and recall are both zero at confidence 0.25 / matching IoU 0.5 for this
small development set. This means none of the returned boxes met the matching
criterion; it does not establish why the detector failed or validate every manual
extent. Earlier center/ROI results measure a different task and are unchanged.

Some images were used in smoke training/validation; the later 16 Getty images
were not trained on but come from an already-inspected recording. None of these
numbers establishes independent generalization. **Keep this checkpoint rejected.**
The result supports expanding reviewed data and recording diversity before a
meaningful new training protocol, rather than integrating or tuning this model.

Local receipts/results remain outside Git in the conversation artifact folder:

- Protocol: ball-box-evaluation-protocol-20261029.json; SHA256
  b8209920f2e3a15c83e4bbb73cbf367bde6bbabec46beb7f1c2b31d52aa31a83.
- Report: ball-box-evaluation-result-20261029.json; SHA256
  92266b2c206622613f20c55e449340bcfe1217c9389bfc52a68b01bd0d74a019.
- Package snapshot: ball-box-evaluation-packages-20261029.json; SHA256
  73642c52c3f10edb524973cc8f4c0f3a41206fd5a054b4a023378c40ddd9c404.

The report's protocol hash and per-frame/per-recording totals were rechecked.
This checkpoint changes measured documentation only; the previously verified
139-test application/evaluation suite is unchanged. No contact/rally implementation
or runtime model promotion occurred.

## Explicit inference size and class declarations

The default remains 640; --image-size 960 selects a separate recorded contract.
Numeric class names are not inferred to mean ball. --expected-class-name permits
only an exact declared name match after source annotation inspection. See
neural-input-contract.md for source-frame point filtering, the actual 960 diagnosis
and the rejected publisher candidate. These changes do not overwrite prior results.
