# Manual frame calibration verification

Story: choose a local clip in the browser, mark its four table corners, send only
geometry to the local API, and display a geometry check with explicit limitations.

## Automated checks

14 Python tests passed using the project's Python 3.12 environment. Coverage:
HTTP workspace/assets and private-file restrictions; host/origin rejection;
video decoding and limits; timestamp fallback; perspective mapping; invalid
corner counts, out-of-bounds/nonfinite points, duplicates, winding, self-crossing,
collinearity, concavity, insufficient area, and invalid API payloads.

## Browser evidence

Tested the actual supplied 768x432, 12.012-second MP4 through the browser file
chooser on the local server at port 8014. Video metadata appeared correctly.
Four source-coordinate corners were entered using the keyboard controls.
The calibration API returned success and the interface displayed:

> Table geometry checked for this frame. Camera stability and ball tracking have not been evaluated.

Starting and pausing playback cleared all corners and disabled calibration.
The page displayed the explicit cleared-calibration message. Browser error/warn
logs were empty during that flow. The narrow layout stacked the video and
controls without horizontal overflow in the inspected screenshot.

This verifies geometry preparation, not ball detection, contacts, rallies, or
camera stabilization. Corners were selected for a smoke check; no ground-truth
contact locations or evaluation accuracy were established. Videos and reference
images are not tracked. The source-coordinate alternative and pointer mapping were both exercised. A
pointer click in the resized preview produced source coordinates (187.3, 84.6),
consistent with the expected approximate (188, 84) click location. Removing the
video cleared metadata and corners; selecting the same file again restored the
preview without old corners. Seeking to the end also cleared selected corners.
