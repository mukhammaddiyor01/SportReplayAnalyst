# Ball candidate pilot

The source preview is not stored here. ball-pilot.json contains its SHA-256,
source dimensions, a coarse image search window, and 18 approximate manual labels.
Six visible blurred-ball centers and three negative search-region frames belong
to each split. Centers were read from original frames before candidate scoring;
coordinate grids were used for the later held-out frames. Labels are not expert
reviewed. The 8px tolerance accommodates blur/annotation ambiguity; it is not a
contact-location accuracy requirement.

The tuning positives are frames 150, 155, 160, 165, 170, 175, with negatives 90,
93, 96. Held-out positives are 180, 183, 186, 210, 220, 225, with negatives 99,
102, 105. These adjacent segments share one video and are not independent players,
cameras, or environments. They are a pilot, not a generalization benchmark.

The first tuning pass found many tiny white line/player fragments. The minimum
connected-component area was increased from 3 to 35 reference-image pixels using
the tuning split only. All other initial thresholds stayed unchanged. Parameters
were frozen before running held-out scoring; do not adjust them against held-out
failures without defining a new evaluation split and reporting that change.

```bash
.venv/bin/python -m evaluation.evaluate_ball_candidates /path/to/clip.mp4 --split tuning
.venv/bin/python -m evaluation.evaluate_ball_candidates /path/to/clip.mp4 --split held_out
```

The search window is a coarse image rectangle, not table-plane calibration.
Candidate extraction does not compensate for camera movement or infer 3D motion.
Returned bright moving blobs may be clothing, hands, lines, or the ball. Saturated
candidate lists and multiple candidates remain ambiguous. Neither detections nor
single candidates establish physical contacts or rallies. Do not commit footage,
frames, or generated analysis output. Record only honest aggregate evidence in docs.
