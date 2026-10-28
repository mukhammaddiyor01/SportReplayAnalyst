# Tracking evaluation: source inventory and timing diagnostics

Checkpoint: 2026-10-28. This supports stages 1–2 of the README completion plan.
It is not a completed independent benchmark or a model-promotion decision.

## Recording inventory

| Recording group | Source and preparation | Exposure / permitted use |
| --- | --- | --- |
| getty-recording | Original SHA256 de1be132d44deb1be6e932585b2b029a8092a3fc4aa65c6774368ec5cad28fc1; 768×432, 360 declared frames | All existing point and box intervals inspected; detector tuning and smoke training used this recording. Development/regression only. Sampled camera movement prevents assuming fixed calibration. |
| lion-recording | Original SHA256 2194ffcd9f572fde42861c1ffd56d3844bb69dd5d9349880d3f33aa02d36f18e; analysis SHA256 36b9bea5db38130117c8e57900b87ef771ef4610a1c59632e5427ec81e61ffb2 | First 180 decoded frames cropped to 720×860, original y=analysis y+140, original index unchanged. Prefix inspected; 20–49 and 60–89 evaluated, 20–29 used for smoke validation. Development/regression only; camera stability uncertain. |
| Independent evaluation | No fresh recording admitted yet | Source identity, recording relationship, camera suitability and untouched evaluation intervals still need to be recorded. |

Related crops, excerpts and transcodes retain the original recording group.
Unscored frames from an inspected recording are not an independent recording.
Full-source hashes identify bytes, not independence. No personal paths or images
are stored in this inventory; local artifacts remain outside Git.

## Implemented diagnostic definitions

The sequence evaluator processes preceding decoded frames as inference context,
without consulting labels. Only labeled consecutive source frames are scored.
OpenCV and optional YOLO evaluation share score_sequence and its timing rules.

- Correct observation: an actual associated observation within the annotation's
  frozen source-pixel center tolerance. Predictions never count.
- Wrong observation: an actual observation outside that tolerance on a visible label.
- Missed observation: no associated observation on a visible label. Wrong and missed
  frames both form visible loss runs; uncertain/negative labels end such runs.
- Candidate coverage and negative candidate counts remain separate from associated
  observation counts. Candidate presence does not establish a false track.
- sample_span_seconds: last loss-sample timestamp minus first loss-sample timestamp.
  A single lost sample has zero span. This is not full loss/occlusion duration;
  the exposure duration and subframe boundaries are unknown.
- visible_reacquisitions: a correct sample after a visible loss run, with a preceding
  correct sample and no intervening uncertain/negative label. Report source-frame
  bounds, elapsed time from the preceding correct sample, tracker-ID equality and
  explicit trail break. Wrong observations can occur inside the loss run.
- Same tracker ID is diagnostic, not independently established physical identity.
  Leading/trailing losses cannot establish a bounded recovery. Uncertain/negative
  labels reset continuity; no recovery interval is inferred across them.
- Timestamps must be finite, nonnegative and strictly increasing. Do not substitute
  frame-count/FPS estimates inside the scorer. Reader fallback provenance remains
  in the underlying records; fallback timing is not independently measured PTS.

## Real-video regression check

Normal full_shape_v1, consecutive_v1, existing ROI and 8px tolerance; no tuning.
Previously inspected labels were rerun on 2026-10-28:

| Source / sequence | Correct / visible | Wrong | Negative observations / labels | Longest loss sample span (seconds) | Bounded visible reacquisitions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Getty 140–169 | 24/26 | 0 | 0/0 | 0 | 1 |
| Getty 230–259 | 27/29 | 0 | 0/0 | 0.033367 | 1 |
| Getty 195–224 | 27/28 | 0 | 0/0 | 0 | 1 |
| Getty 80–109 | 0/0 | 0 | 0/30 | 0 | 0 |
| Lion 20–49 | 0/30 | 0 | 0/0 | 0.483333 | 0 |

Zero spans can mean isolated lost samples; they do not mean no loss. Zero
reacquisitions can mean no correct observations at all, as in Lion. Do not average
these columns into a reliability score. Existing observation totals are unchanged.
Raw reports are owner-managed local artifacts, not committed analysis output.

## Next independent experiment prerequisites

Before accessing held-out model outputs, record fresh source/group hashes,
intervals, camera conditions, manual ROI/calibration policy, timestamp provenance,
independently reviewed point/box/negative labels, and excluded uncertain intervals.
Freeze numerical matching tolerances, per-recording coverage/false-observation/gap
acceptance limits and model/tracker settings before evaluation. The current pilot's
8px tolerance is not automatically valid for another resolution or blur extent.

Report counts/denominators and loss/recovery evidence per recording, alongside
runtime and overflow; keep detection and association results separate. Define
box matching and false-positive metrics before a quality YOLO run. No independent
acceptance experiment is frozen or passed yet: fresh footage and label review
are still needed. Contact and rally metrics belong to later, separately labeled
experiments; these loss intervals are not sports events.
