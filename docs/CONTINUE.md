# Continue Sports Replay Analyst

Checkpoint: 2026-10-28. Data assembly and a real local YOLO smoke-training/evaluation
flow are verified. 131 Python tests pass. Normal app tracking remains OpenCV.
Use README.md as the single current status/priority guide; this file is the handoff.

## Repository and working rules

Speak Uzbek; code/interface/docs are English. Work in SportReplayAnalyst, not the
unrelated AI_Python conversation workspace. Read AGENTS.md; inspect Git status.
Private repository: https://github.com/mukhammaddiyor01/SportReplayAnalyst.git.
Small verified feat:/fix: commits and pushes belong on develop. master stays
42a6008. Never force push, publish user footage/weights, or deploy.

## What works

Local video review, source-frame stepping, manual table geometry, bounded spawned
jobs, cancellation/expiry, sampled camera-drift checks, experimental OpenCV
associations and observed-only 2D trails/gap review. No physical speed/3D, contacts,
rally inference, identity, scoring, live video or multiple cameras are implemented.

The separate /labels workspace reviews exact prepared PNGs, with a 4x pixel loupe,
source-coordinate boxes, explicit negatives/uncertainty, download and resume.
Images stay in the browser. The dataset CLI prepares/exports outside Git.
See ball-annotation.md for the verified browser flow and privacy distinction.

## Current model/data state

- Getty original SHA256: de1be132d44deb1be6e932585b2b029a8092a3fc4aa65c6774368ec5cad28fc1.
  Source 360 frames, 768×432. See appearance-detector.md and tracking-loss-diagnostics.md.
- Lion analysis MOV SHA256: 36b9bea5db38130117c8e57900b87ef771ef4610a1c59632e5427ec81e61ffb2.
  First 180 decoded frames cropped to 720×860; original mapping/provenance is in
  lion-footage-review.md. The full portrait original exceeds the app’s height cap.
- All old point labels and Lion 20–49/60–89 have been inspected; they are development
  evidence. Do not present reused data as fresh validation.
- Current manual labels contain Getty 18 visible/6 full-frame negatives/2 uncertain
  and Lion 7 visible/3 uncertain: 25 boxes, 6 negatives, 5 uncertain. The 2026-10-28
  increment is separate from the frozen 15-box smoke dataset. Labels remain
  single-reviewer development evidence; independent review and more recordings
  are still missing.
- evaluation.training_dataset verifies exports and rejects train/val group,
  source-byte, PNG and exact-decoded-pixel overlaps plus duplicate source indices.
  Recording IDs must connect related crops/transcodes; hashes cannot prove independence.
- Fixed smoke dataset: Getty 8 train, Lion 7 val. Local dataset manifest SHA256:
  6930f363aae65977b16afb6b5ad02eadc7ae081a8b5b1de2bd41863165e09b2c.
- Real YOLO11n custom class0 training completed 2 CPU epochs. best.pt SHA256:
  3d0809efe1419a41de8b035e5098371e1066966f9ed7759a8c64d600a186e6cd.
  Both trainer validation epochs reported zero precision/recall/AP. The fixed
  source-point evaluation found no confirmed observations and many false candidates.
  This checkpoint is NOT promoted. See model-development.md for exact results.
- The optional YOLO evaluator defaults to COCO class 32; use --ball-class 0 for the
  custom single-ball model. Normal workers do not import torch/Ultralytics.

## Local artifacts and environment

The conversation’s visualization artifact folder holds the Lion MOV, both prepared
bbox review bundles, v2 label JSONs, v3 reviewed exports, ball-training-smoke-v1,
ball-training-run-v1 (weights/run.json/results.csv), and ball-trained-smoke-evaluation.json.
These are outside Git. Numeric manual pilots and measured docs alone are committed.
The optional model environment and initial YOLO11n weight file are temporary and
may need recreation using requirements-yolo.txt and the pinned official checksum.
See yolo-benchmark.md for download provenance/license. No startup downloads.

The last project server is 127.0.0.1:8014; check before starting another. Port 8000
belongs to another project. Restarting ends temporary video review jobs. Annotator
labels are tab-local until downloaded; saved exports/weights do not expire with jobs.

## Saved portfolio and user preferences

The owner requested a develop push and durable handoff on 2026-10-27.
Implementation through b44e96a and generated portfolio visuals through 8445ada
were already committed/pushed before this handoff. The worktree was clean when
checked. Last verified application suite: 127 passing tests; no application code
changed during this documentation-only checkpoint.

Three purpose-focused original AI concepts are saved in portfolio-assets:
cover, detection/association/review workflow, and manual annotation/local YOLO
preparation. They are 1672×941 PNGs with concept captions; no user footage was
uploaded to the image generator. Exact prompts are retained in purpose-prompts-v2.md.
The user rejected a long portfolio write-up and prefers a concise 3-page case
study: one large image, short title, one compact paragraph and a few facts/features
per page. The accepted English copy/image mapping is in portfolio-assets/case-study.md.
Keep conversation Uzbek, portfolio/UI/docs English, and avoid unverified accuracy
or deployed-neural-detector claims. No portfolio site or public demo was deployed.

## Next action

Follow the owner's four-stage completion plan in README.md:

1. Reliable tracking across videos: baseline, recording inventory, independent
   evaluation protocol and source-timed association checks.
2. Useful YOLO model: reviewed data, frozen quality-training protocol, comparative
   evaluation and qualified worker integration; then repeat stage 1 verification.
3. Table contacts: independent interaction evidence, uncertain candidates,
   deduplication and event evaluation before replay markers.
4. Rallies: explicit start/end/gap/truncation rules and independently evaluated
   intervals before presenting durations.

Immediate work remains stages 1–2 data review: more recordings and independent
box/negative review. Preserve recording groups and untouched evaluation data.
Do not tune the rejected smoke checkpoint or call it useful. No contact/rally
inference until tracking and independent interaction evidence support it.
The stage numbers describe deliveries; stage 2 can be necessary to complete stage 1.

## Quick verification

```bash
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8014
```

Model commands and current milestones are in README.md; frozen experiment details
are in model-development.md. Previous dated checkpoints remain in Git history.

## Logic organization checkpoint (2026-10-28)

Read AGENTS.md and this handoff before resuming. README.md now maps the existing
runtime and offline data flows to their implementation files, and defines the
ordered evidence gates from reviewed data to worker integration and eventual
contact/rally rules. The next action is still data review, not model promotion or
new UI. Full-frame training negatives require full-frame review; old ROI negatives
cannot be reused as full-frame labels without that review. No application behavior,
thresholds, labels or model settings changed in this documentation checkpoint.

## Data increment (2026-10-28)

Exact prepared Getty frames 230:260:3 received 10 source-coordinate visible-extent
boxes after full-frame, enlarged crop and box-overlay inspection. Frames 80:110:5
received 6 explicit full-frame not-visible labels after full-image review, not
conversion from old ROI negatives. Numeric labels are in getty-box-expansion.json
and getty-negative-pilot.json. Images, manifests and verified exports remain in
the conversation artifact folder outside Git. Same getty-recording/source group;
these previously inspected intervals are development material, not a fresh split.
No training, threshold tuning or worker change was performed. Frozen smoke results
remain unchanged. Next: independent review and more recording diversity before
freezing a meaningful new training/evaluation experiment.

## Four-stage scope agreed (2026-10-28)

The owner explicitly requested the four deliveries listed above. README.md is the
single completion plan with tasks, dependencies and evidence gates for each.
This checkpoint organizes future work; none of the four quality gates is newly
completed. No runtime, training settings or annotations changed. Last executed
application suite remains 127 passing tests from the data-increment checkpoint.

## Tracking timing checkpoint (2026-10-28)

Sequence scoring now reports visible-loss sample spans and bounded reacquisitions
using real source timestamps, and rejects invalid/non-increasing times. Uncertain/
negative frames reset continuity; leading/trailing losses do not invent recovery.
Both offline OpenCV and YOLO use this scorer; normal worker tracking is unchanged.
See tracking-evaluation.md for the source inventory, exact metric semantics and
real-video regression table. Getty counts stayed 24/26, 27/29, 27/28 with zero
negative observations on 30 labels; Lion stayed 0/30 with a 0.483333s loss sample
span. Four added tests and the full 131-test suite pass. No model was trained.
An independent-video-path question was asked in chat; check for the owner's answer.
If none is supplied, there is no new independent source. Continue useful development
work without describing reused recordings or repeated review as independent evidence.
