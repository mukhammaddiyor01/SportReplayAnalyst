# Portfolio visuals

Original AI-generated artwork made with the built-in image_gen tool. These are
concept presentations, not real screenshots or measured detector/tracker output.
No user footage, extracted frames or Getty preview was uploaded to the generator.

## Recommended purpose-focused set

All three PNGs are 1672×941 pixels. Use the cover as the project thumbnail/hero,
then the workflow and manual-label images in the case study.

| Image | Portfolio role |
| --- | --- |
| [Purpose cover](sports-replay-purpose-cover-v2.png) | Table tennis replay, a candidate ball and sparse experimental 2D observations |
| [Workflow](sports-replay-workflow-v2.png) | Candidate detection → 2D association → frame-by-frame review |
| [Manual labels](sports-replay-labeling-v2.png) | Source-frame box annotation and preparation for local YOLO experiments |

Keep the concept/experimental captions when publishing. Missing-observation gaps
are deliberately left unconnected. The annotation image does not claim that a
useful neural detector is deployed. No contact/rally inference, physical speed,
3D reconstruction or accuracy metrics are presented. Pair these illustrations
with actual screenshots when demonstrating working application behavior.

Exact prompts and targeted refinements: [purpose-prompts-v2.md](purpose-prompts-v2.md).
The final refinement removed pale dashed prediction-like bridges from both
tracking visuals while preserving the two separated observed segments.

Concise three-page English case-study copy: [case-study.md](case-study.md).

## Earlier preparation-only concepts

The earlier assets are retained without replacement:

- sports-replay-cover.png: original cover for the preparation/inspection stage.
- sports-replay-features.png: table calibration, background frame inspection,
  cancellation, clearing and local-processing concept.
- prompts.md: their original generation prompts.

These historical concepts do not depict the later ball-review workflow.
