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
