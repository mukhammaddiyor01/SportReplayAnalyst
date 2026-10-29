# Data-limited development fine-tuning v1

Frozen 2026-10-29 before training in response to the owner's request to complete
the core functionality faster. This is an explicit new development experiment,
not an enlargement or relabeling of the old 2-epoch smoke run. Single-reviewer
labels remain insufficient for a general reliability claim or contact/rally work.

## Fixed data and settings

- Train: Getty/Lion, 38 visible boxes and 6 explicit full-frame negatives, 2 groups.
- Validation: reserved OpenTTGames test_2, 10 manually reviewed visible boxes.
  It remains excluded from gradient training; checkpoint selection consumes these
  validation images, so they are not untouched final-test evidence.
- Dataset purpose development_finetune_v1; SHA256
  7eea1ebe713416a4757d5736af1ff893e9384f578a668068fb983737ae048dd6.
- Official YOLO11n base SHA256
  0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1.
- Profile development_v1: 60 epochs, image 960, batch 4, CPU, 4 torch threads,
  first 10 layers frozen, AdamW lr .001 / final fraction .01, warmup 2 epochs.
- Other smoke arguments retained: seed 0, deterministic option, workers 0,
  no AMP/cache/plots, no geometric/mosaic/mixup/flips; brightness HSV gain .15
  is the sole added augmentation. Exact arguments are in train_ball_model.py.
- Offline inference/training sockets blocked, sync disabled; system Arial copied
  locally beforehand. No startup/model downloads by workers. Weights and data stay local.
- No result-driven threshold/epoch sweep, relabeling or recording reassignment.
  Run/checkpoint hashes and actual results are recorded after completion.

Local pre-training protocol SHA256:
bb5b09b1d2327cca81f9c6d2443db91638c6e3e4df78221af666bd9e048a3d5d.
The artifact folder holds ball-development-dataset-v1, ball-development-protocol-v1.json
and the verified yolo11n-base-v8.4.0.pt. Old smoke artifacts remain unchanged.

## Evaluation and integration gate

Use the existing box evaluator at image 640, confidence .25, match IoU .5 and
NMS IoU .7, class 0. A candidate needs at least 8/10 external box matches with
precision >=.8. Also evaluate existing external point intervals with the fixed
ROI [300,400,1550,750], 8px tolerance and consecutive tracker: candidate coverage
>=.8 and correct associations >=.7 of 72 references, with at most 2 wrong observations.
No worker integration from box scores alone. These are prospective engineering
gates, not measured achievements or proof of generalization. External points are
model-aided and manual boxes are single-reviewer; independent review remains missing.

No contact/rally inference is justified by this run alone. Preserve existing
OpenCV tracking and the rejected smoke checkpoint. If a gate fails, report the
failure rather than promoting the best-looking reused-data result.

## Explicit commands

```bash
.venv/bin/python -m evaluation.training_dataset --train /path/to/train-exports --val /path/to/reserved-export --purpose development_finetune_v1 --output /path/to/new-dataset
python -m evaluation.train_ball_model /path/to/new-dataset --profile development_v1 --model /path/to/yolo11n.pt --model-sha256 CHECKSUM --output /path/to/new-run
```

Smoke remains the default with its original 2-epoch arguments. Profile and dataset
purpose must match before model loading. Existing dataset role and leakage checks
still apply. 146 automated tests pass without optional ML dependencies.

## Actual result

The fixed 60-epoch CPU run completed in about 609 training seconds. best.pt SHA256:
b17b03fedc380cb2115cdbea71135cbf15955dad42f08a5e4e836e8c1d28a255.
last.pt SHA256:4367aacdf0e629fac95ee9b9d39e166f890ff92d26c2d68e63ad8c61a049cd54.
The frozen 640/full-image box evaluation returned 0 TP, 0 FP and 10 FN on external
validation: precision null (no predictions), recall zero. The earlier smoke model's
82 false boxes fell to zero, but absence of predictions is not useful detection.

| Existing source-point interval | Correct / visible | Wrong |
| --- | ---: | ---: |
| Lion 20–49 | 26/30 | 0 |
| Lion 60–89 | 0/12 | 0 |
| Getty 140–169 | 16/26 | 0 |
| Getty 230–259 | 26/29 | 0 |
| Getty 195–224 | 0/28 | 0 |
| OpenTTGames test_2 combined | 0/72 | 0 |

The fixed ROI-cropped 640 point evaluator found nearby candidates on 6/72 external
references, without confirmed associations. Getty's 30 search-region negatives
had no observed associations. These intervals overlap training/development data;
they do not establish generalization. Candidate gates failed; do not integrate.
Normal OpenCV tracking and the original smoke run remain unchanged.

Local evaluation report SHA256:
d0bfc9796e37b00672875fa26c7d970cccd7d8fe3fd444522c6f950a3a694130.
Run receipt SHA256:ae1ccbec3b48513524d57f1d97daa46ddbd474f5286a17b639392bd7771f36ec.
All raw reports/logs/weights remain outside Git in ball-development-run-v1 and
ball-development-evaluation-v1.json. No post-result parameter sweep occurred.
