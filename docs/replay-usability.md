# Replay workflow refinement

The interface keeps the existing sports-replay palette: canvas #f3f6f8, white
surface #ffffff, ink #243746, replay blue #183d51, action teal #36758a, and
corner amber #ffb469. Avenir Next/Segoe UI remain local system fonts. Left-aligned
controls and source-timed review rows support inspection instead of adding
unmeasured statistics or decorative dashboard cards.

The upload toolbar now precedes the video at all widths. On wider screens the
video/review occupy the main column and calibration/analysis share a side panel.
Below 800px the order is source, video, preparation/analysis, then gap review.
The narrow layout keeps the upload entry visible before the player and avoids
placing review intervals ahead of the controls needed to generate them.

Track ball is the primary analysis action. Source selection and existing geometry
checks still gate it; no calibration or job lifecycle rule changed. A current-state
label and next-action hint follow actual clip, calibration and job state. Inspection
without tracking and detailed numeric output are available under Inspection details.
Video requirements/privacy remain accessible before processing, with local-copy
retention and original-file handling also stated directly beside the analysis.

Review pauses/seeks and brings the video into view, including on narrow screens.
A one-frame interval uses singular copy. The observation-only trail and uncertainty
rules are unchanged. Requirements and privacy text, cancellation, result clearing,
keyboard focus and reduced-motion behavior remain available.

Verification: 94 existing Python tests passed; JavaScript syntax checks passed.
HTML inspection found no duplicate IDs or unbalanced tags. Actual browser flow
covered source upload, numeric corners, geometry check, gated Track ball, progress,
completion, opening/closing inspection details, review seek to missing frame 149,
and normal seek back to associated frame 180. The result had 360 decoded frames
and 11 review intervals, processing counts rather than accuracy. Clear result
removed the earlier result before the final run. At the observed 544px viewport,
page width was also 544px, with no horizontal overflow. Browser warning/error logs
were empty. Screenshot proof stays outside Git; the final local review result
remains under ordinary retention. Wider breakpoints are defined in CSS and were
not visually exercised in this increment.

## Source-frame stepping

Playback now includes Previous frame / Next frame buttons (−1/+1). They remain
disabled until a matching tracking result with usable source presentation times
is available. The controls reuse the overlay's actual ordered frame records and
timestamp lookup, pause playback, and seek inside the neighboring source frame's
recorded time interval. The midpoint avoids browser decoder rounding at exact
frame boundaries; the following timestamp (or clip duration at the last frame)
bounds the interval. They do not estimate a step from nominal FPS, interpolate positions,
or turn a missing/predicted record into an observation. Clip/result clearing
disables them; source timing fallback or dimension mismatch keeps them disabled.

Left/Right arrows work when focus is in the playback control group, except the
native position slider. Modifier shortcuts and coordinate inputs retain their
normal behavior. Frame stepping clears frame-local corners through existing seek
handling. Hiding the trail still leaves the current source frame identifiable.
The narrow layout puts the timeline below the playback buttons to avoid crowding.

Actual browser verification on the supplied video confirmed frame transitions
149 → 148 → 149 → 150, including the missing observation at 149. The initial
exact-boundary seek displayed 147 when 148 was requested; seeking inside the
recorded frame interval fixed that observed browser rounding issue. Both arrow
keys were exercised in playback controls. At source frames 0 and 359 the outward
step button was disabled; stepping 359 → 358 → 359 stayed bounded. With the trail
hidden, source frame status and stepping still worked. A Right arrow in the native
slider moved 6.006s to 6.007s while remaining on frame 180, confirming the shortcut
did not hijack its controls. The final next-frame action showed associated frame
181. Browser warning/error logs were empty; screenshot proof remains outside Git.
All 94 Python tests and the changed script's syntax check passed. This increment
does not improve detector accuracy or infer a contact/rally.
