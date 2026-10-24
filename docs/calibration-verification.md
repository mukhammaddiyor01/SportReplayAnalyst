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

## Workspace redesign verification

The replay desk layout was visually reviewed in the browser at desktop and
narrow viewport settings, then the temporary viewport override was reset.
The video surface and inspector sit side by side on desktop and stack on narrow
screens. Narrow-layout DOM measurements showed no horizontal document overflow.

The real local video was selected through the redesigned file control. Entering
four source corners updated the visible count to 4 / 4; checking geometry returned
the expected success message. Playback cleared the points, restored the empty
corner hint and 0 / 4 count, and disabled calibration. Browser error/warning logs
were empty during calibration. All 14 existing Python checks passed.

No new tracking, contact, or rally behavior was introduced. Screenshots remain
outside the repository because the loaded preview contains user-provided footage.
