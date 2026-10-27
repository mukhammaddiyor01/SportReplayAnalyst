# Neural detector development: fixed smoke protocol

The critical path is manual boxes → recording-separated dataset → local training
→ frozen detector/track evaluation → independent validation → worker integration.
Do not implement contacts/rallies to compensate for absent ball measurements.

## Frozen before training (2026-10-27)

Two source-only visual passes produced15 approximate manual boxes: Getty8 and
Lion7;5 uncertain extents are excluded, no negative examples were labeled.
Source crops/grids were inspected, not model-generated bounding boxes. Lion’s
original20,22,29 boxes are unchanged; new labels cover21,23,27,28. The uncertainty
at24 is retained, with25/26 also excluded. Getty140/167 remain uncertain. A second
extent pass expanded clipped blur tails at Getty152/155 and Lion27/28 before any
training predictions were inspected. All labels are single-reviewer development
evidence and need independent review; neighboring frames are correlated.

The dataset assembler verifies each exported image hash, decoded dimensions and
YOLO label against its manual provenance. It rejects shared recording IDs, source
hashes, PNG hashes or identical decoded pixels across splits, and duplicate source
indices within one split. Explicit recording grouping must still connect related
crops/transcodes: hashing cannot detect every near-repeat or shared recording.
Uncertain/unreviewed frames remain excluded. No automatic random split is used.

Frozen development split: Getty8 visible images for train; Lion7 visible images
for val. Both recordings have already been inspected and reused; val here is a
trainer configuration, not untouched generalization evidence. The tiny dataset
without hard negatives can only test pipeline operation.

- Dataset manifest SHA256:6930f363aae65977b16afb6b5ad02eadc7ae081a8b5b1de2bd41863165e09b2c.
- Initial weights: official YOLO11n assets v8.4.0, SHA256
  0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1.
- Optional environment is pinned in requirements-yolo.txt. Local CPU only, no
  network connections, sync disabled, no model/package download during training.
- Single ball class0; image640; batch4;2 epochs; workers0; no AMP/cache/plots.
- SGD lr.001, final LR fraction.01, momentum.9, decay.0005, no warmup.
- Seed0, deterministic option; no mosaic/mixup/copy-paste/flips/geometric/color
  augmentation. Exact arguments live in evaluation/train_ball_model.py.
- No parameter sweep, dataset relabeling from predictions, or quality claim based
  on the smoke run. Keep model weights, caches and generated results outside Git.

The existing checksum-verified YOLO evaluator keeps COCO class32 by default;
--ball-class0 supports the trained single-ball head. Detection and association
must still be measured separately with source timestamps. A training completion
or a checkpoint file is not evidence that the tracker is useful.
