# Sampled camera movement and frame calibration

## Implemented check

Compare the first decoded source frame to samples every 0.5 seconds and the final
frame. OpenCV tracks distributed Shi-Tomasi features using pyramidal LK flow,
checks forward/backward consistency, and estimates a robust partial affine scene
transform. The center play/net band and a lower-left overlay region are excluded
from initial feature selection to reduce overlay/player dominance.

The adapter returns correspondence/support measurements. A plain Python service
requires at least 12 inliers, 0.65 inlier fraction, 0.12 convex-hull coverage, and
0.35 span on both image axes. These are experimental parameters, not calibrated
confidence probabilities. Processing width is bounded at 640; displacements are
converted back to original source pixels along each axis.

A supported estimated frame-corner displacement over 0.5% of the source diagonal
flags movement. The metric is extrapolated displacement of the image boundary
under the fitted scene transform, not a measured 3D camera position or a table
contact coordinate. The thresholds live in backend/config.py.

- movement_detected: reliable evidence exceeds the threshold; reuse is blocked.
- uncertain: support/coverage is inadequate or timing gaps are too large; reuse is blocked.
- no_movement_detected: at least two supported comparisons with no inconclusive
  samples and no excess timing gap; manual alignment review is still required.

The browser already clears table corners on playback and seeking. This report
reinforces that frame-local behavior; it never enables unattended calibration
reuse. No stabilization or compensation is performed.

## Real-video evidence

The supplied preview decoded all 360 frames. Across 24 comparisons, all 24 met
the configured evidence requirements. Maximum estimated frame displacement was
13.064 source pixels against a 4.406-pixel experimental threshold. The result was
movement_detected, with calibration reuse blocked. No manually measured camera
motion ground truth was used, so these are estimates, not an accuracy claim.

## Verification and limits

41 total automated checks passed after integration. Camera-specific checks use
fixed textured scenes, known translation at a resized processing resolution,
rotation, a small moving foreground patch, blank/occluded frames, insufficient
feature distribution, timing gaps, and persistence of prior movement evidence.

A dominant moving foreground, moving screen overlay, large viewpoint change,
rolling shutter, nonplanar scene, weak texture, and motion between sample times
can invalidate or escape this estimator. An uncertain result is not a stable
camera. Review footage and use a better fixed-camera clip before claiming reliable
cross-frame calibration. Detection/tracking and contacts/rallies remain separate.
