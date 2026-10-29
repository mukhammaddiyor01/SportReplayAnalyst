# Explicit neural input contract and published candidate diagnosis

Checkpoint: 2026-10-29. These are offline diagnostics, not worker promotion or
completion of the tracking/contact/rally milestones. 149 automated tests pass.

## Input geometry

The original evaluate_yolo default remains roi_crop /640. It crops the source ROI,
runs inference and adds the crop origin once. Historical benchmark results retain
that definition. It is not interchangeable with inference on training-like full frames.

The explicit --input-mode source_frame passes the complete decoded source image
to the model, then filters returned source-coordinate box centers against the ROI.
No crop offset is added. Boxes may cross an ROI boundary while their centers remain
inside; centers on the right/bottom exclusive boundary are excluded. Filtering
occurs before the 12-candidate association cap, so detections outside the ROI do
not consume that budget. A 100-detection inference cap is conservatively treated
as overflow even if some returned boxes lie outside the ROI.

Both box/point evaluators accept --image-size 640 or 960, recording the choice.
Default remains 640. The explicit source_frame/960 diagnosis matches development
training's full-frame/960 input convention; it is a new protocol after the original
gate failed, not an unchanged-protocol improvement or a fresh validation result.
No confidence sweep or model retraining occurred in this diagnosis.

Actual development-v1 checkpoint result at source_frame/960:

| Source interval | Correct / visible | Wrong |
| --- | ---: | ---: |
| Lion 20–49 | 30/30 | 0 |
| Lion 60–89 | 0/12 | 0 |
| Getty 140–169 | 18/26 | 0 |
| Getty 230–259 | 25/29 | 0 |
| Getty 195–224 | 0/28 | 0 |
| External test_2 combined | 1/72 | 0 |

The external intervals had 5/72 near-reference candidates. External 10-box scoring
still had zero predictions/TP/FP and 10 FN. Getty's 30 search-region negatives had
no associated observations. The perfect Lion development interval overlaps training
and nearby frames; it does not establish general tracking reliability. The gate
still fails and normal workers remain full_shape_v1.
Local report ball-source-frame-result-v1.json SHA256:
22c4176e612cb2ea6cba1e24cae0322889833e0a7a1f33f977c3360bd65f66f0.

## Explicit class mapping

Default semantic names remain ball / sports ball. Models whose labels are numeric
are refused unless --expected-class-name explicitly matches the selected class.
A human must first verify that semantic mapping from the publisher's annotations;
the flag is a declaration, not automatic proof that a numeric class means ball.
Names/IDs are recorded in both reports; invalid/incorrect mappings fail before
prediction. No app setting or generic relaxed class filter was introduced.

## Published table-tennis YOLO candidate

We inspected [Haroun Rhim's repository](https://github.com/harounRhim/pingpong-detection-yolov8)
and [v0-archive release](https://github.com/harounRhim/pingpong-detection-yolov8/releases/tag/v0-archive).
The repository declares MIT; Ultralytics runtime/model-origin terms remain relevant.
No publisher source code, dataset, images or weights are redistributed here. The
publisher's claimed metrics are not adopted as our project's measured performance.

The 280,751,641-byte release archive matched GitHub's published SHA256
b4d149aee8e2ec659c44e63f26f00053fa5b9502f389464a86ae46eab25a7172.
Selected runs/detect/train2/weights/best.pt from the only multi-epoch run before
inspecting any target predictions. Archive args request 50 epochs; CSV has 14 rows,
and the checkpoint stores epoch=12. We do not describe that as a verified 12-epoch
run length based on README wording. Extracted checkpoint SHA256:
f012e2f7290e942acc1852998d44d02991f9b82d4bf1d1a79bc39d7c83f314b3.

Publisher class names are numeric. Source image/label inspection showed class 0's
box centered on the visible ball; other labels describe scene objects. The first
attempt stopped at the semantic-name guard before inference. After recording this
mapping, a single source_frame/640, confidence .25, class 0/name 0 diagnosis ran.
No threshold sweep or code from the publisher was used.

Result: Lion development 2/30 correct; Lion review 0/12; Getty three positive
intervals 0/83; external 0/72. No wrong associated observations were scored and
Getty negative observations remained 0/30. External boxes had no predictions,
0 TP/FP and 10 FN. Upstream training-data overlap is unknown, and all target
references are reused. This model is not adopted or integrated.
Local report pingpong-community-mapped-result.json SHA256:
9a21b5099f060aea5c5073b77ea76ab413b9980b0eff94954d1b55eed34d8d85.

The next useful work is representative reviewed training data and independently
checked extents, not another model-family detour or fabricated contact/rally output.
