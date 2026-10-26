# Experimental bright-ball candidate baseline

## What is implemented

The OpenCV adapter compares consecutive original BGR frames inside an explicit
coarse image search window. It combines low-saturation brightness, positive
intensity change, local contrast, and connected-component size/shape filters.
It accepts short white blur streaks rather than requiring a circular ball.
It returns original source coordinates, component area, and bounding boxes.
No learned model, external service, or model download is used.

A bright moving candidate is not a confirmed ball. Multiple candidates remain
ambiguous; candidate overflow is explicitly marked. The output cap is 12 per
frame. There is no temporal identity, track, prediction, trajectory, bounce
classification, or rally calculation. The same frozen adapter is now composed with the separate temporal
service in experimental worker/browser tracking. It does not assign identity
or create trajectories on its own; see docs/temporal-tracking.md.

Named experimental parameters live in backend/config.py. The reference source
width is 768; area, extent, and contrast-neighborhood size scale with source
width. The initial small-component threshold generated many line/clothing
fragments in tuning. Raising minimum reference area from 3 to 35 removed those
tuning fragments. This rejects very small balls too; it is not a general detector.

## Annotated pilot and frozen evaluation

See evaluation/ball-pilot.json and evaluation/README.md. The source SHA-256 is
verified before scoring. There are 18 approximate manually labeled frames: each
split has six visible blurred-ball centers and three search-window negatives.
Positive centers use an 8px matching tolerance to accommodate blur and manual
labeling. No expert reviewed the labels, and no contact points were annotated.

After tuning, thresholds were frozen before held-out scoring:

| Split | Visible labels | Visible frames with a nearby candidate | Negative frames | Extra/wrong candidates | Ambiguous frames |
| --- | ---: | ---: | ---: | ---: | ---: |
| Tuning | 6 | 6 | 3 | 0 | 0 |
| Held out | 6 | 6 | 3 | 4 | 3 |

Neither split overflowed the candidate cap. All three held-out negative frames
returned no candidates. The extra held-out candidates occurred in frames 183,
186, and 210 around the moving player/white clothing. These errors were retained
in the report; the held-out set was not used for another threshold adjustment.

This is candidate coverage on a tiny, adjacent, single-video pilot. It is not
tracking accuracy, detector confidence, or evidence of broad generalization.
No percentage is presented as a quality guarantee. Full-flight/occlusion labels,
additional fixed-camera footage, and a larger independent evaluation are needed.

## Running the real evaluation

```bash
.venv/bin/python -m evaluation.evaluate_ball_candidates /path/to/clip.mp4 --split tuning
.venv/bin/python -m evaluation.evaluate_ball_candidates /path/to/clip.mp4 --split held_out
```

The reader preserves original frame indices/timestamps. The search window is an
image rectangle, not a homography or a true table-plane location. Camera drift
is not compensated here. The separate camera check blocks unattended calibration
reuse on this sample. No user footage or derived frame is stored in Git.

## Verification

51 automated checks passed after adding the baseline. Candidate-specific tests
cover moving bright balls, blur streaks, static white overlays, ambiguity,
rejection of tiny/dim/large/long objects, source scaling, invalid input geometry,
explicit overflow, duplicate-candidate scoring, and source-video identity.

A local diagnostic compared frame 180 (one ball-like candidate) with frame 183
(two candidates, including a false player/clothing fragment). It is stored outside
the repository with UI evidence. The live browser inspection also displayed
Movement detected / Frame-local only and the camera warning after the worker
processed the supplied clip; its error/warning logs were empty.

## Next step

Add a plain Python temporal association service: conservative initialization,
source-time-based motion gates, explicit ambiguity, short-gap recovery, and reset
rules. Keep predictions distinct from observations. Evaluate it independently of
candidate coverage before showing a trustworthy trajectory. Contacts and rallies
remain later stages; 2D direction changes alone do not establish table contact.
