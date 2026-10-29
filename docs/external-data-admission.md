# OpenTTGames source admission and fixed OpenCV diagnosis

Checkpoint: 2026-10-29. Stage 1 now has a third recording source for diagnosis.
It is not a completed tracking benchmark, YOLO training dataset or event detector.

## Source and declared terms

[OSAI's official OpenTTGames page](https://lab.osai.ai/) describes 120 FPS full-HD
recordings, model-aided ball-coordinate labels and manually marked game events.
It declares the dataset license as CC BY-NC-SA 4.0. We selected test_2 from that
publisher, retaining attribution to OSAI and Voeikov, Falaleev and Baikulov (2020).
Only local copies are kept; no third-party video, frame or annotation is committed.

The official points describe locations, not visible-extent boxes. Missing keys
mean unannotated frames; they cannot become negatives or inferred positions.
The publisher documents (-1,-1) for absence. No such entries occur in this prefix.
Event annotations are source references, not outputs of our application. No contact
or rally implementation was added. Do not create YOLO squares around these points.

A [third-party YOLO subset card](https://huggingface.co/datasets/weslien/topspin-opentt-ball-subset)
was inspected but not imported: its boxes are fixed 32px squares around coordinates,
which does not satisfy this project's reviewed visible-extent box policy.
No new model family, external code or pretrained checkpoint was adopted.

## Source identity and bounded preparation

- Original test_2.mp4: 225,118,372 bytes; SHA256
  91df783ab4d26bf350faffaefabe9fb6c172584dfd053a866729b11cc3261c43.
- Official test_2.zip markup: 897,976 bytes; SHA256
  c692014ca9074d331700385e4c0b5e0bd32968123bf001fe8b1c9b2e64ac142d.
- Accepted analysis AVI: 43,880,226 bytes; SHA256
  5f64f0836ea57cb47498db9866f1779dbff29c8b78ef606795d10c467adbd638.

These are locally computed receipt hashes, not publisher-provided checksums.
Download was explicitly bounded to 256 MiB/180 seconds. The oversized original
was never submitted to the app. Existing 100 MiB/60s/1920×1080/120 FPS limits remain.

The original declares 3600 frames; only the first 256 were decoded/verified here.
They were written one-for-one to MJPEG AVI at 120 FPS with native 1920×1080 geometry.
There is no crop/resize or index offset. Verified original times are i/120 seconds;
all accepted output times matched, last 2.125s, with zero FPS fallbacks. Reencoding
is lossy: maximum frame-wise mean absolute decoded channel difference was 3.024.
This is a pixel-difference diagnostic, not a geometric error/accuracy guarantee.
AVI browser playback has not been verified; this is an accepted offline source.

Two earlier native MOV attempts were rejected without weakening validation:
passthrough declared 258 frames but decoded 256; H264 reencoding reported
120.018313 FPS. Do not use them or the old MOV-derived admission-review bundle.
The accepted file is openttgames-test2-prefix-cfr.avi. Exact PNGs for future manual
box review are in openttgames-test2-cfr-review (15 images, indices 88:243:11).

The accepted prefix passed full bounded decoding and five sampled camera-motion
comparisons. No movement above the existing threshold was found (maximum estimated
0.488px); calibration reuse still requires table-alignment review. This does not
certify the remainder of the source or physical table geometry.

## Frozen point-reference diagnosis

Before any detector output on this source, source-only anchors at frames
88,99,110,176,231 were checked visually against the external points. The remaining
references were not independently reviewed. A protocol fixed full_shape_v1,
consecutive_v1, source-only coarse ROI [300,400,1550,750], 8px center tolerance and
intervals 88–121,173–189,226–248. There was no ROI/threshold sweep. Frames 188/189
lie outside the ROI and were excluded as uncertain before scoring, not converted
to full-frame negatives. Missing keys were not filled or interpolated.

| Interval | Scored positive references | Excluded | Near-reference candidates | Correct observations | Wrong observations | Longest loss sample span (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 88–121 | 34 | 0 | 0 | 0 | 0 | 0.275000 |
| 173–189 | 15 | 2 | 0 | 0 | 0 | 0.116667 |
| 226–248 | 23 | 0 | 0 | 0 | 0 | 0.183333 |

All 72 scored references were missed, with no bounded reacquisitions or candidate
overflow. There were no scored negatives, so this cannot establish a false-track
rate. These are agreements with external model-aided coordinates, not independently
verified accuracy. Do not infer contact or rally timings from these loss spans.

The source was not used in local training/tuning before this run. Its first prefix
and stated label intervals are now inspected and evaluated; they must not later
be presented as untouched validation. Upstream pretrained-model data overlap is
unknown. Keep the entire openttgames-test2 recording group out of training while
using it for evaluation. Generalization needs more than one short external prefix.

Local protocol SHA256:
45760df74cad99a9b8513fb2466d3be81eb62b63bfd3a2bed4c080259757c232.
Local result SHA256:
667c7e02f421774e24852ecfd5fbf9607e76d38cac0f55413db353707d3dd93f.
All downloads, decoding receipts, external labels and analysis results remain in
the conversation artifact folder outside Git, with openttgames-test2 prefixes.

## Code and next action

Sequence reports now retain source hash, dimensions, ROI, tolerance and annotation
method. Their limitation text no longer misidentifies external references as
single-reviewer manual labels. The provenance regression test and all 140 tests
pass without ML packages. Normal workers, thresholds and user annotations are
unchanged. No model was trained or promoted.

Review actual visible extents before any YOLO export, preserving source/license
provenance and recording separation. More independent label review, training
recording diversity and a frozen quality-training protocol remain necessary.
The 38 existing manual boxes and 6 negatives from Getty/Lion remain the only
reviewed YOLO data; this admission adds no fabricated training boxes.

## Reserved manual box review and first YOLO box diagnosis

The 15 prepared full images were manually inspected, followed by nearest-neighbor
crops and visible-extent box overlays. Ten approximate boxes were retained at
88,99,110,132,154,165,176,187,198,209. Frames 121,143,220,231,242 remain uncertain
because visibility or extent could not be identified sufficiently; none became
an invented negative or a point-centered square. The frame 99 lower box edge
was refined to avoid including the table line before export/inference. Single
reviewer only: these boxes still need independent review and are not expert truth.
No YOLO predictions were used to construct or refine them. The source already
had an OpenCV point diagnosis, so this is consumed evaluation/diagnostic material.

Both source manifest and review declare intended_use=evaluation_only. The real
export contained exactly 10 class-0 labels; 5 uncertain images were excluded.
An attempted train assembly using that export was rejected before output creation.
Training data remain Getty/Lion 38 boxes, 6 negatives and 9 uncertain extents;
this source contributes a separate 10-box/5-uncertain evaluation-only review.

Before its first YOLO box inference on this recording, a local protocol froze the
review/export hashes, existing smoke best.pt SHA, confidence .25, match IoU .5,
NMS IoU .7, image size 640, CPU/class 0 and max_det 100. All 10 full prepared images
were processed offline. Result: TP 0, FP 82, FN 10; precision/recall zero, no cap
reached. There are no explicit negative images in this export, so no negative-frame
false-positive rate is established. No tuning, training or model promotion followed.
This checkpoint remains unsuitable. No contact/rally inference is justified.

Local files in the artifact folder (not redistributed in Git):

- openttgames-test2-manual-box-review.json; SHA256
  1d3dcb8bf1f03ba17b994b4627973d113cb54ae28a03041cd79af0476f5ad5bc.
- openttgames-test2-manual-box-export/ with manifest/review provenance.
- openttgames-test2-box-protocol.json; SHA256
  9b7357dcb8f5bcfd72edd8a060146a4c565ad301fb4e84b0c89ae4591150da6f.
- openttgames-test2-box-result.json; SHA256
  47b9597b83ad02c5d313296f9355727aaf95f11ffb04b7beaebb48f02b4e8472.

The application still uses OpenCV. Dataset tools now preserve/validate declared
roles through exports and prevent reserved train membership; the trainer rechecks
roles, and box reports retain them. All 144 tests pass; actual reserved export and
train rejection were exercised separately from fixtures. Future work needs diverse
training recordings and independent extent review, with this recording reserved.
