# Development dataset v2 — 2026-11-04

## Actual review and export

Completed the remaining 11 prepared OpenTTGames game_1 frame reviews. Four
additional visible extents at source indices 74, 89, 119 and 209 were read from
full-source image contact sheets, then checked in nearest-neighbor pixel crops
and source-coordinate rectangle overlays. Seven other frames remain uncertain;
none was converted to a negative. Existing three boxes and three uncertain labels
were preserved in a new version, leaving the original review/export unchanged.

The resulting 17-frame review contains 7 visible boxes and 10 uncertain frames.
All seven visible examples exported successfully; uncertain frames were excluded.
Labels are approximate, single-reviewer development evidence, not independent
truth. No inference model supplied boxes. No point-to-radius conversion was used.
The four new boxes were located visually; neighboring-frame sampling is correlated.
No contact or rally evidence was assigned from these images.

Source remains the admitted 256-frame, native 1920x1080, 120 FPS CFR prefix,
SHA256 aff7ef9d916b287f29e8e169bb8090d52f724c15ffa142de1e75265b1d212b90.
Original source was only partially fetched; whole-original integrity is not claimed.
OSAI OpenTTGames / Voeikov, Falaleev, Baikulov (2020), declared CC BY-NC-SA 4.0;
see external-data-admission.md. Images, labels and derivatives remain outside Git.

## Verified assembled dataset

The new ball-development-dataset-v2 uses the existing six Getty/Lion reviewed
exports and the seven-box game_1 export. It does not include the earlier three-box
game_1 export again. Assembly and the actual trainer check_dataset preflight passed:

| Split | Visible | Explicit negative | Recording groups |
| --- | --- | --- | --- |
| Train | 45 | 6 | Getty, Lion, OpenTTGames game_1 |
| Val | 10 | 0 | Reserved OpenTTGames test_2 |

All image hashes, decoded pixels, source indices, labels and effective roles were
rechecked. The reserved group stays outside gradients. Validation has already
selected checkpoints in earlier runs and is not an untouched final test. No new
training, predictions, quality comparison or application change occurred here.
The normal worker remains full_shape_v1; contact and rally stages remain open.

Local artifact basenames:

- openttgames-game1-manual-box-review-v2.json — SHA256
  991803e46f71b12f919696013bdd616a992e9636bd55731e9005154c1577184b
- openttgames-game1-manual-box-export-v2 — 7 verified images/YOLO labels.
- ball-development-dataset-v2/dataset.json — SHA256
  2bebeab6563d5a8bee14a0def51d3e87321286f658af76cefe7f20aef12c33e5
- ball-development-dataset-v2-receipt.json — actual counts and preflight status.
- game1-expansion-full-20261104.png, game1-expansion-extents-20261104.png and
  game1-expansion-overlays-20261104.png — local visual review aids.

Next: freeze a v2 run/evaluation protocol using the full-frame input contract before
training. Keep the previous dataset/checkpoints/reports unchanged. This small data
increment cannot establish general tracking reliability or justify event inference.


## Frozen v2 training/evaluation protocol (before training)

One run of the unchanged development_v1 profile: 60 epochs, full-frame 960 input,
CPU, batch 4, 4 Torch threads, seed 0, frozen first 10 layers, AdamW lr .001,
no geometric augmentation; all other parameters match development-finetune-v1.md.
Start from the same official YOLO11n base, SHA256
0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1.
Use the assembled v2 dataset above. Preserve the old run and start a new output.

Evaluation uses source_frame/960, confidence .25, NMS IoU .7, box matching IoU .5
and existing 8px center references. Compare directly to the saved v1 full-frame
report on the same Getty/Lion/external intervals. This is a reused diagnostic,
not independent validation. No threshold sweeps or post-inference label edits.

The diagnostic gate requires all of:

- At least 8/10 external box matches and precision at least .8.
- External candidate coverage at least .8 and correct associations at least .7
  of 72 visible references, with at most 2 wrong observations.
- No observations on the existing Getty negative interval.
- No Getty/Lion sequence loses correct observations or increases wrong observations
  relative to the prior source_frame/960 report.

Passing this gate alone does not establish general reliability or qualify contact/
rally inference; independent final evaluation and bounded worker checks still apply.
Training and scoring run offline with socket connections blocked. The optional ML
environment is separate from the app. No input footage is sent to model services.

Local frozen ball-development-protocol-v2.json SHA256:
2818897060068c7886237a3a891176fa48a82cf962b0c2015fd4db0ac5800760.
