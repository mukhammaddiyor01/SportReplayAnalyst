# Continue Sports Replay Analyst

Checkpoint: 2026-10-29. Data assembly and a real local YOLO smoke-training/evaluation
flow are verified. 149 Python tests pass. Normal app tracking remains OpenCV.
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
  and Lion 20 visible/7 uncertain: 38 boxes, 6 negatives, 9 uncertain. Later
  development increments are separate from the frozen 15-box smoke dataset.
  Labels remain single-reviewer development evidence; independent review and more recordings
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

## Box evaluator checkpoint (2026-10-29)

Added evaluation.evaluate_box_detector for full prepared-image YOLO box metrics,
separate from source-center/ROI temporal scoring. It validates reviewed exports,
rejects duplicate source frames, verifies local model SHA, blocks sockets, scores
confidence .25 / IoU .5 and reports TP/FP/FN plus per-recording totals and saturation.
See box-detector-evaluation.md for semantics, limits and command. The normal app,
training recipe and annotations are unchanged; the smoke checkpoint stays rejected.
139 tests pass; 31 real reviewed frames (25 boxes/6 negatives) revalidated. Synthetic
framework composition was tested; no real inference or training was rerun because
the old temporary optional ML environment is gone. Preserve the local weights;
recreate the pinned isolated environment before real box evaluation. New footage
and independent label review remain missing. Do not claim stage 1/2 completion.

## Real box inference checkpoint (2026-10-29)

The optional ML environment was restored in the temporary sra-yolo-20261029 folder,
with the five pinned requirement versions and pip check passing. App env still
has no torch/Ultralytics. Existing smoke best.pt SHA was verified; fixed export
hashes and settings were saved before running actual full-frame CPU inference.
All 31 reviewed images were processed with socket connections blocked: Getty
0 TP /45 FP /18 FN, Lion 0 TP /36 FP /7 FN. Total 0 matching boxes from 25 visible
references, 81 FP, all 6 negatives with predictions, no detection-cap frames.
Confidence .25, match IoU .5; no sweep, relabeling, training or model promotion.
See box-detector-evaluation.md for exact result/protocol/package-snapshot hashes.
All three local receipts are in the artifact folder, prefixed ball-box-evaluation.
The optional env can expire again; preserve receipts and existing weights.
This is development diagnosis, partly reusing training/validation images, not fresh
validation or a useful model. 139 tests remain last verified; runtime code unchanged.
Next remains reviewed data, independent label review and new recording diversity
before freezing a meaningful quality-training experiment. Do not implement contacts
or rallies to bypass absent ball measurements.

## Lion label expansion (2026-10-29)

Added 13 manually reviewed source-image visible-extent boxes: 30,33,36,39,42,45,48
and 63,66,69,72,78,81. Frames 60,75,84,87 remain uncertain; no Lion negatives were
inferred from unclear visibility. Sources were exact prepared PNGs, full-image
inspection, enlarged nearest-neighbor crops and extent overlays; no model boxes
were consulted. Existing pilots/point labels remain unchanged. Single reviewer,
not independent review or fresh validation. The frame 78 box crosses the old ROI right edge, and frame 81 lies fully beyond
it; both are visible in the full prepared image, so label scopes differ.
Numeric labels: evaluation/lion-box-expansion-a.json and lion-box-expansion-b.json.
Artifact bundles are lion-box-expansion-a/b-20261029; exports are
lion-box-expansion-a/b-export-20261029. Exports verified 7+6 visible labels; 4 uncertain excluded. The six reviewed
exports together validate as 44 usable images: 38 visible boxes and 6 negatives,
with no duplicate source indices. No training or inference was rerun. The earlier
31-image evaluation and frozen 15-box smoke dataset remain unchanged. No runtime
code changed; last application suite remains 139 passing tests. Next: independent
label review and additional recording diversity before quality-training design.

## Third recording admission (2026-10-29)

Official OSAI OpenTTGames test_2 was downloaded locally with a bounded receipt.
See external-data-admission.md for primary sources, declared CC BY-NC-SA terms,
source/markup/prefix hashes, preparation failures and exact results. No data or
third-party annotations were committed. Original 225 MB exceeds the app byte cap.
Accepted openttgames-test2-prefix-cfr.avi is 43,880,226 bytes, 256 decoded frames,
1920×1080 at 120 FPS, first/last times 0/2.125, zero fallback. One-to-one MJPEG
reencoding preserves geometry/index/CFR time but is lossy. Both MOV attempts are
invalid for the app; only the CFR AVI passed existing checks. Browser playback of
AVI is unverified. Current review PNGs: openttgames-test2-cfr-review (15 images).
Source-only anchors checked; external model-aided references are not expert/manual
extent truth. Frozen baseline ROI [300,400,1550,750], 8px point agreement and three
intervals scored 0/72 correct/near-reference candidates; 188/189 excluded outside
ROI as uncertain, no negative frames scored. No tuning or model promotion.
This recording was not used in local training; its prefix/reference intervals are
now consumed diagnostic data, not untouched validation. Keep openttgames-test2
out of training while evaluating on it. No automatic point-to-box conversion.
Sequence reports now retain actual annotation/source provenance instead of a
hardcoded manual-label claim. 140 tests pass. Getty/Lion manual data remain
38 boxes/6 negatives/9 uncertain; third-party point references add no YOLO boxes.
Next: actual extent review with source/license provenance and more training
recording diversity, while reserving separate untouched evaluation evidence.

## Reserved external boxes and dataset roles (2026-10-29)

Reviewed all 15 OpenTTGames admission PNGs: 10 approximate visible-extent boxes,
5 uncertain (121,143,220,231,242), no negatives. Review JSON, crop/overlay checks,
YOLO export and result/protocol files stay local with openttgames-test2 prefixes;
see external-data-admission.md for exact hashes and source attribution. No external
derivative numeric labels were committed. These are evaluation-only, not added
to the Getty/Lion development totals (38 boxes/6 negatives/9 uncertain).
First fixed real YOLO box run on these 10 frames: 0 TP /82 FP /10 FN, no cap reached.
Confidence .25 /IoU .5; no retraining, sweep, box edits after inference or promotion.
The old smoke checkpoint is still rejected; normal worker unchanged.
Prepare now accepts --intended-use evaluation_only. Manifest/review flags combine
conservatively; browser downloads omitting a role cannot downgrade the original
manifest. Exports preserve effective roles, assembly rejects reserved train examples,
and the trainer rechecks before loading weights. Unknown roles rejected; old
unmarked files default to development. Val use allowed but consumes model-selection
evidence. This metadata check is not a global or tamper-proof source registry.
144 tests pass; actual 10-label export and attempted train rejection verified.
Next: new training-recording diversity and independent extent review. Keep the
entire OpenTTGames test_2 group reserved; do not repurpose it as training to improve
its own result. Source/license metadata and owner-managed artifacts remain local.

## Development fine-tuning v1 (2026-10-29)

Owner requested faster completion; moved from repeated smoke scoring to an explicit
data-limited development profile. Commit c1d59de adds --purpose development_finetune_v1
and --profile development_v1; smoke defaults remain unchanged and profile/purpose
must match. 146 tests passed. Actual 60-epoch/960/CPU/AdamW/freeze10 run completed,
train Getty/Lion 38 visible+6 negative, val reserved OpenTTGames test_2 10 boxes.
Protocol and actual results: development-finetune-v1.md. best.pt SHA starts b17b03fe.
Lion development improved to 26/30 correct, but Lion review stayed 0/12; external
box gate 0/10 (no predicted boxes), points 6/72 nearby candidates /0 correct.
Several Getty intervals regressed vs OpenCV. Gate failed, no runtime promotion.
Val selected this checkpoint; no untouched test claim. Actual artifacts include
ball-development-dataset-v1, ball-development-run-v1, ball-development-evaluation-v1.json.
Official YOLO11n base restored and pinned in artifact yolo11n-base-v8.4.0.pt.

A separate official OpenTTGames game_1 TRAINING source is now locally admitted:
openttgames-game1-prefix-cfr.avi (45,642,102 bytes), SHA256
aff7ef9d916b287f29e8e169bb8090d52f724c15ffa142de1e75265b1d212b90.
256 sequential frames, 1920×1080/120 FPS, 0..2.125 seconds, zero fallback. Its full
5,572,649,632-byte source was NOT downloaded or fully hashed. Only first 32 MiB plus
480,316-byte MP4 metadata tail were fetched with verified HTTP ranges/version.
The incomplete sparse source is explicitly named incomplete-sparse-source; never
submit it to app or claim full-file integrity. Source range hashes/ETag/transform
are in openttgames-game1-admission.json; markup SHA is
a4109881b1e848340bced411a2da5b21de3794ebcb52454e50443fe3ce2d345c.
Source/license attribution remains OSAI OpenTTGames / CC BY-NC-SA 4.0. No data
redistribution. Prepared 17 review PNGs, indices14:256:15, are in
openttgames-game1-cfr-review. Only four full frames inspected so far; no manual
boxes saved or added to training. Keep this group distinct from reserved test_2.

## Input contract and published-model diagnosis (2026-10-29)

Added explicit evaluate_yolo --input-mode source_frame (default legacy roi_crop),
with --image-size 640/960 in both point and box evaluators. Source boxes keep native
coordinates; filter ROI centers before association cap, conservatively withhold
when full-frame detection limit100 reached. Numeric model names require explicit
--expected-class-name and prior semantic mapping; defaults stay ball/sports ball.
149 tests pass. Normal worker unaffected. See neural-input-contract.md for actual
results: own model source_frame/960 gives Lion development30/30 but review0/12,
external1/72, several Getty regressions. External boxes0/10; no promotion.
An additional public table-tennis YOLO checkpoint was source/digest checked and
class0 verified against publisher labels, then evaluated once at source_frame/640:
Lion2/30, review0/12, Getty0/83, external0/72. Not adopted. Publisher archive, extracted
weights and metadata/results stay outside Git with pingpong-community prefixes.
Its upstream overlap is unknown; do not import author claims as our accuracy.

Game_1 manual pilot now saved locally as openttgames-game1-manual-box-review.json:
3 visible boxes44/104/149, 3 uncertain14/29/134; remaining11 prepared frames remain
unreviewed. Points only helped locate crops; extents manually read from pixels,
no fixed-radius boxes or target-model predictions. Export verified3 labels in
openttgames-game1-manual-box-export. Review SHA256:
c6df53ff9b730b97041cdd040fccb11d5cfc3d6c80085d45d4ee3ab3b7d3e8bb.
This pilot is development-only and NOT yet used for training; it adds 3 local boxes
beyond the prior Getty/Lion38, preserving the frozen development-v1 dataset/run.
No external data or derivative numeric labels entered Git. Source license attribution
remains in local provenance. More representative training data and independent
extent review are still needed; no contacts/rallies were implemented.

## Training dataset v2 assembled (2026-11-04)

Read AGENTS and existing handoff before continuing stages 1–2. Completed all 17
prepared game_1 reviews: 7 visible boxes, 10 uncertain; four new visible extents at
74/89/119/209 checked in full-image/crop/rectangle overlays, other seven newly
reviewed frames remain uncertain, no new negatives. Source/model/license rules
unchanged; no external derivative labels entered Git. Original three-box review
and frozen v1 experiments preserved. See development-dataset-v2.md for artifacts,
source/review/dataset hashes and limitations. Local export-v2 has 7 examples.
Assembled ball-development-dataset-v2: 51 train images (45 visible, 6 negative)
across Getty/Lion/game_1, same 10 reserved test_2 val boxes. Actual assembler and
trainer check_dataset preflight passed all integrity/role checks. Dataset SHA256
2bebeab6563d5a8bee14a0def51d3e87321286f658af76cefe7f20aef12c33e5.
No new training/inference occurred; optional temporary YOLO environment from
October 29 no longer exists. Recreate separately if training; normal app unaffected.
Latest automated suite remains the earlier 149 passed; data-only change verified
through real export/assembly/trainer preflight instead of rerunning unrelated tests.
Next: freeze v2 full-frame training/evaluation protocol before training, preserve
old results and evaluation-only split. Contacts/rallies still not implemented.
