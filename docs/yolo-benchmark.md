# Local YOLO baseline protocol (2026-10-27)

Run an isolated, offline pretrained-model diagnostic in response to the user’s
YOLO/PyTorch question. This is not a runtime detector replacement or training run.
The app requirements/environment stay unchanged. Ultralytics source/model terms:
https://github.com/ultralytics/ultralytics/blob/main/LICENSE (AGPL-3.0); see also
https://www.ultralytics.com/license. No weights or user frames are redistributed.

Frozen before inspecting predictions:

- Official YOLO11n COCO weights, assets release v8.4.0, yolo11n.pt, 5613764 bytes.
- SHA256 from GitHub release API: 0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1.
- Explicit manual download URL: https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt.
- Ultralytics 8.4.190, torch 2.14.1, torchvision 0.29.1 in a separate local environment.
- CPU, one torch thread, input 640, confidence .25, NMS IoU .7, class 32 sports ball.
- Crop the same annotation search rectangle without manual resizing. Ultralytics
  returns boxes in original crop coordinates; add the crop origin exactly once.
- Retain up to 12 candidates; request 13 so overflow is explicitly ambiguous.
  No brightness, motion, area or shape filters on neural detections.
- Feed every preceding decoded frame to the original consecutive BallTracker;
  retain source timestamps/indices. Predictions are never scored as measurements.
- Evaluate the existing Lion 20–49,60–89 and Getty dense labels at tolerance 8px.
  All these labels are already inspected development/regression data, not a fresh
  neural-model validation set. Keep Lion 90–179 unscored in this baseline.
- Report near-center candidate coverage, actual associated observations, false
  candidates and latency separately. Center labels do not support bounding-box AP.
  No parameter sweep, fine-tuning, or promotion based on this one diagnostic.

Current point labels are approximate single-reviewer visible-blur centers.
Training needs independently reviewed bounding boxes, negatives, and splits by
independent recording/session rather than random neighboring near-repeat frames.
Do not fabricate boxes from a constant radius around these centers. If this
pretrained baseline fails, propose a table-tennis-specific dataset/fine-tuning
step instead of presenting generic COCO recognition as solved ball tracking.

## Actual result and decision

The official file matched the release SHA256 and byte count before it was loaded.
The benchmark ran locally with socket connections blocked, YOLO_OFFLINE=true,
sync disabled, and no image/result saving by Ultralytics. Optional environment:
Python 3.12.14, Ultralytics 8.4.190, torch 2.14.1, torchvision 0.29.1, NumPy 2.5.4,
OpenCV 4.13.0.92. The app environment did not receive torch/Ultralytics. Results and
weights remain outside Git. No training, GPU/MPS trial, threshold sweep or browser
integration was performed.

| Labels | Visible | YOLO candidate within 8px | YOLO correct associations | Default OpenCV correct associations |
| --- | ---: | ---: | ---: | ---: |
| Lion 20–49 | 30 | 0 | 0 | 0 |
| Lion 60–89 | 12 | 0 | 0 | 0 |
| Getty 140–169 | 26 | 0 | 0 | 24 |
| Getty 230–259 | 29 | 0 | 0 | 27 |
| Getty 195–224 | 28 | 0 | 0 | 27 |
| Getty 260–299 | 37 | 5 | 0 | 37 |
| Getty 300–339 | 23 | 0 | 0 | 20 |
| Getty 0–29 | 25 | 0 | 0 | 19 |

The default OpenCV column is the matching frozen baseline in
sparse-motion-protocol.md. All source/ROI/tolerance settings match; YOLO uses
semantic neural boxes instead of brightness/motion components. No YOLO association was confirmed in the labeled intervals; it therefore has zero wrong observed associations as
well. This does not indicate accurate tracking: all visible labels were missed
by the associated-output metric. There were 5 unmatched retained candidates on
Getty visible labels (1 in 260–299, 4 in 300–339), using one expected point and 8px
tolerance; these are not standard bounding-box false positives. Both Getty negative
intervals total 46 frames with zero YOLO candidates. Lion has no negative labels.
Uncertain labels are excluded. These data do not establish whole-video accuracy.

Each evaluation processed all prior context: 50,90,260,300,340,30 decoded frames.
Local arm64 Mac, single CPU thread: mean predict calls after the first evaluation
were 24.3–27.4ms; the first 50-frame evaluation averaged 76.9ms and its first call
took 2683.3ms. Timing includes inference wrapper/preprocessing/first-call setup,
excludes model loading/decoding, and is not end-to-end application FPS.

**Do not promote this pretrained baseline.** It is substantially less useful than
the current default on Getty and does not resolve Lion. This result applies to
this exact model/crop/640/.25 configuration; it does not prove that fine-tuned,
other-size or other-family YOLO models cannot work. The next neural step is
reviewed table-tennis bounding boxes with hard negatives and independent-source
validation, followed by fine-tuning. Keep the existing temporal service and local
worker/privacy rules when replacing candidate extraction.

## Reproduction

Create a separate Python 3.12 environment and install requirements-yolo.txt there;
do not install it over the app’s headless OpenCV environment. Explicitly download
the pinned URL above outside Git; verify its published SHA256. The evaluator
requires an existing local .pt file and matching hash, never a model name that
would trigger download. Configure local YOLO_CONFIG_DIR and MPLCONFIGDIR before
running; the evaluator sets offline mode and disables sync.

```bash
python -m evaluation.evaluate_yolo /path/to/lion-table-first-180.mov --annotations evaluation/lion-development.json --model /path/to/yolo11n.pt --model-sha256 0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1
```

Repeat with the other annotation files and corresponding source. 114 application
and pure-Python/adapter tests passed, including model-integrity rejection, crop
coordinate mapping, invalid neural boxes and explicit overflow. These checks
require no optional ML dependency or model download. Real-model measurements
above were a separate offline run. Contact/rally inference remains unimplemented.
