# Neural detector development: fixed smoke protocol

The critical path is manual boxes → recording-separated dataset → local training
→ frozen detector/track evaluation → independent validation → worker integration.
Do not implement contacts/rallies to compensate for absent ball measurements.

## Frozen before training (2026-10-27)

Two source-only visual passes produced 15 approximate manual boxes: Getty 8 and
Lion 7; 5 uncertain extents are excluded, no negative examples were labeled.
Source crops/grids were inspected, not model-generated bounding boxes. Lion’s
original 20,22,29 boxes are unchanged; new labels cover 21,23,27,28. The uncertainty
at 24 is retained, with 25/26 also excluded. Getty 140/167 remain uncertain. A second
extent pass expanded clipped blur tails at Getty 152/155 and Lion 27/28 before any
training predictions were inspected. All labels are single-reviewer development
evidence and need independent review; neighboring frames are correlated.

The dataset assembler verifies each exported image hash, decoded dimensions and
YOLO label against its manual provenance. It rejects shared recording IDs, source
hashes, PNG hashes or identical decoded pixels across splits, and duplicate source
indices within one split. Explicit recording grouping must still connect related
crops/transcodes: hashing cannot detect every near-repeat or shared recording.
Uncertain/unreviewed frames remain excluded. No automatic random split is used.

Frozen development split: Getty 8 visible images for train; Lion 7 visible images
for val. Both recordings have already been inspected and reused; val here is a
trainer configuration, not untouched generalization evidence. The tiny dataset
without hard negatives can only test pipeline operation.

- Dataset manifest SHA256:6930f363aae65977b16afb6b5ad02eadc7ae081a8b5b1de2bd41863165e09b2c.
- Initial weights: official YOLO11n assets v8.4.0, SHA256
  0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1.
- Optional environment is pinned in requirements-yolo.txt. Local CPU only, no
  network connections, sync disabled, no model/package download during training.
- Single ball class 0; image 640; batch 4; 2 epochs; workers 0; no AMP/cache/plots.
- SGD lr .001, final LR fraction .01, momentum .9, decay .0005, no warmup.
- Seed 0, deterministic option; no mosaic/mixup/copy-paste/flips/geometric/color
  augmentation. Exact arguments live in evaluation/train_ball_model.py.
- No parameter sweep, dataset relabeling from predictions, or quality claim based
  on the smoke run. Keep model weights, caches and generated results outside Git.

The existing checksum-verified YOLO evaluator keeps COCO class 32 by default;
--ball-class 0 supports the trained single-ball head. Detection and association
must still be measured separately with source timestamps. A training completion
or a checkpoint file is not evidence that the tracker is useful.

## Actual run and decision

The 2-epoch CPU run completed and wrote best.pt and last.pt outside Git. Initial
model and dataset hashes matched the frozen values. Both trainer validation
epochs reported zero precision, recall and box AP. best.pt SHA256 is
3d0809efe1419a41de8b035e5098371e1066966f9ed7759a8c64d600a186e6cd.
The optional environment stayed separate from the app; no sockets were permitted.

A fixed 640/.25 class 0 evaluation then processed every prior source frame, using
the existing point-label ROI, 8px tolerance and consecutive tracker. No parameter
was changed after seeing the outputs:

| Development labels | Visible | Near-center candidates | Correct associations | Visible frames with candidate overflow |
| --- | ---: | ---: | ---: | ---: |
| Lion 20–49 |30 |2 |0 |30 |
| Lion 60–89 |12 |0 |0 |12 |
| Getty 140–169 |26 |1 |0 |0 |
| Getty 230–259 |29 |0 |0 |0 |
| Getty 195–224 |28 |1 |0 |0 |

On Getty 80–109, all 30 labeled search-region negatives had candidates, although
none became observed associations. Overflow means the detector returned at least
13 candidates and the bounded adapter withheld association. Thus a few near-center
candidates do not demonstrate improved detection. No independent-video, identity,
whole-clip or contact/rally result is claimed. The data are tiny, correlated,
positive-only and already used for development/model selection.

**Do not promote this model.** The verified result is an operational local
prepare→review→export→grouped dataset→train→evaluate pipeline. Useful neural
tracking still needs more reviewed data and hard negatives, followed by a new
frozen experiment. Do not enlarge this smoke run or sweep confidence values and
present the best reused-data result as validation.

## Reproduction and ownership

After preparing and manually reviewing source bundles:

```bash
.venv/bin/python -m evaluation.training_dataset --train /path/to/getty-export --val /path/to/lion-export --output /path/to/new-dataset
python -m evaluation.train_ball_model /path/to/new-dataset --model /path/to/yolo11n.pt --model-sha256 0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1 --output /path/to/new-run
python -m evaluation.evaluate_yolo /path/to/lion.mov --annotations evaluation/lion-validation.json --model /path/to/new-run/weights/best.pt --model-sha256 CHECKPOINT_SHA256 --ball-class 0
```

The latter two commands use a separate environment from requirements-yolo.txt.
Existing output directories are refused. Training rechecks the locally generated
YAML, split membership, file counts, image hashes and reviewed labels before
loading the model; arbitrary download YAML is not accepted. A local system Arial
font was made available to the temporary YOLO config directory so no font download
was needed. Local generated datasets, label caches, logs and weights are persistent
owner-managed artifacts outside Git, not one-hour analysis jobs. run.json records
status, initial/dataset hashes, exact arguments and resulting checkpoint hashes.

127 automated tests passed without optional ML dependencies. Added checks cover
cross-split leakage including re-encoded PNGs, altered exports/YAML/labels, source
path injection, non-overwrite and custom class 0→source-coordinate mapping. The
real training/evaluation above is separate evidence, not a mocked unit test.
