# Exact-frame ball annotation

The replay header now links to `/labels`, a separate, local annotation workspace.
It reads prepared PNG frames directly in the browser, without uploading images or
calling a hosted model. This avoids assigning browser video-seek rounding to a
source frame index. The regular replay/calibration/tracking flow is unchanged.

## Prepare, review, export

Use the normal app environment and an output folder outside the repository whose
parent already exists. The output folder must not exist; nothing is overwritten.
The source still has the existing video byte/dimension/FPS/duration limits.

```bash
.venv/bin/python -m evaluation.ball_dataset prepare /path/to/clip.mov --recording-id recording-one --start 20 --stop 30 --output /path/to/review-bundle
```

The stop index is exclusive; optional `--stride` selects decoded indices without
renumbering them. Each PNG is the complete decoded BGR source frame encoded
losslessly, with no resize/crop. Its manifest records dimensions, original video
SHA256, recording group, decoded index, actual timestamp/fallback and PNG SHA256.
Preparation does not certify unseen frames after the requested prefix. A bundle
is bounded to 120 frames, 8 MiB per PNG, 128 MiB total; failed preparation is cleaned.

Open the app’s Label ball frames page. Select manifest.json and its PNGs together.
Checksums are checked before review. Use two opposite corners or numeric xyxy
coordinates around the full visible ball/blur; the 4x pixel loupe helps inspect
its extent. Save ball box explicitly. Unsaved drafts are discarded on navigation.
Do not include racket/hand/line fragments to force a box. Use Uncertain when the
ball or box extent cannot be identified; Ball not visible is an explicit negative.
Unreviewed is different from both states.

Download labels before closing/reloading or replacing the bundle. The tab keeps
labels only in memory; Resume from labels JSON restores labels for the exact
matching recording/source/images. A mismatched import is rejected without
replacing the existing review. No browser storage, server label database or
network upload is used. The JSON download contains numeric labels and provenance,
not images or personal source paths.

```bash
.venv/bin/python -m evaluation.ball_dataset export /path/to/review-bundle --labels /path/to/recording-one-labels.json --output /path/to/reviewed-yolo
```

Export checks label geometry, frame identity, image hashes and decoded dimensions.
Visible labels become one class 0 ball row in normalized YOLO xywh format; explicit
not-visible frames get empty label files. Uncertain and unreviewed frames are
excluded. See the official format:
https://docs.ultralytics.com/datasets/detect/#ultralytics-yolo-format.
`images/`, `labels/` and `provenance.json` are produced outside Git. No data.yaml,
train/validation split or model training is created automatically.

Keep the same recording ID across related excerpts/crops/transcodes. Split by
independent recording/session before training, never random neighboring frames.
Current point-only annotations cannot be exported as training boxes. Do not
invent a radius around a point. A second reviewer and more recordings/negatives
are still needed before treating this as a training/evaluation dataset.

## Verification and initial manual pilot

120 Python tests passed; JS syntax passed. Tests cover normalization, explicit
negative/uncertain handling, duplicate/foreign source labels, invalid/point-only
boxes, changed PNGs, traversal, retained decoded indices/times, short-source
cleanup and non-overwrite. The annotation route/static script return 200 with
existing no-store/CSP policies.

Actual browser flow used the already-inspected Lion frames 20–29, source SHA
36b9bea5db38130117c8e57900b87ef771ef4610a1c59632e5427ec81e61ffb2.
Manually reviewed visible-extent boxes were saved for 20,22,29, and frame 24 was
left uncertain for box extent. Numeric fields and two-corner clicks were both
exercised. Download and resume restored 4/10 reviewed frames; a foreign source
JSON was rejected while retaining the review. Console warnings/errors were empty.
The downloaded JSON was passed to the real CLI exporter: exactly 3 images and 3
normalized class 0 label files, zero label files for uncertain/unreviewed frames,
and split=unassigned. Provenance and media stay outside Git; only manual numeric
labels are retained in evaluation/lion-box-pilot.json. This is a single-reviewer
workflow pilot, not independently reviewed ground truth or a sufficient dataset.
No model was trained and no detector/track accuracy gain is claimed.

The first desktop visual check found a CSS grid-area collision with the replay
sidebar. It was fixed; the source frame now fits the viewport height and the
pixel loupe remains separate from the original image. Desktop browser verification
was performed; responsive CSS is provided but no device-size test was performed.
