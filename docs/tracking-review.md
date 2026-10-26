# Source-timed tracking gap review

Tracking jobs now return review_gaps alongside source-frame records. A plain
Python service groups consecutive records without an associated observation.
Searching, tentative, predicted, and ambiguous states remain unobserved. A
prediction is not evidence of a measured point. The detector/association rules
are unchanged by review summarization.

Each interval preserves first/last decoded index and source timestamp, frame
count, status counts, optional preceding/following track IDs, and the following
observation time when present. Clip start, between observations, clip end, and
an entirely unobserved clip are distinct positions. A single missing frame is
reviewable; its equal timestamp endpoints do not imply zero physical duration.
No inferred duration, contact, occlusion, confidence, or rally boundary is added.
Dense source indices, increasing finite time, and observation/status consistency
are checked before summarization. Empty/fully observed sequences return no gaps.

The replay desk shows real review intervals after successful tracking. A Review
button pauses playback and seeks to the first missing source timestamp. The
observation-only trail therefore stays blank at that missing frame. The active
review indication clears when playback/seeking leaves the interval. One-frame
intervals show one timestamp. Source timing fallback or a playback/source-size
mismatch disables navigation, as it does for the overlay. Legacy job results
without interval metadata ask the user to run tracking again.

Clear result or replacing/removing the clip clears review state. Navigation is
not gated on current manual corner selections because it uses source-video time,
not table geometry. It does not make stale calibration usable. Changing frames
still clears manual geometry through the existing playback behavior.

Six new service tests cover empty/full observations, open clip boundaries, mixed
missing states and irregular source times, a single-frame gap, a wholly unobserved
clip, and invalid sequences. API tests verify gap metadata survives the spawned
worker and JSON response. All 94 Python tests passed; JavaScript syntax passed.

Actual browser verification used the supplied clip and a corner-derived window:
360 decoded frames, 227 associated observations, 11 missing-observation intervals.
Those processing counts are not accuracy, occlusion, contact, or rally counts.
Clicking the 4.972s single-frame interval paused/seeks to source frame 149;
the overlay showed no observation (predicted), with no fabricated marker.
Seeking to 6.006s showed associated frame 180 and cleared the active review
indication. Clear result hid the interval list and removed displayed review state.
The final run reproduced navigation with the single-timestamp display.
Browser warning/error logs were empty; screenshot evidence remains outside Git.

A separate actual source-video HTTP/ASGI upload and spawned worker completed
with 360 records equal to offline tracking. Explicit deletion left zero private
job directories and preserved the original source. The final browser review
result remains available under normal one-hour retention for the user to inspect.
