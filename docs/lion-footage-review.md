# Second-footage baseline review (2026-10-27)

The user supplied a second table-tennis recording, identified by original SHA256
2194ffcd9f572fde42861c1ffd56d3844bb69dd5d9349880d3f33aa02d36f18e.
Container metadata reports 720x1280, 60 FPS, 431 frames (about 7.18s), 2,501,322
bytes. OpenCV actually returned 426 frames, ending at 7.083333s. This discrepancy
is recorded, not repaired or treated as proof of corruption. Full-source integrity
is not certified. Height exceeds the application's existing 1080px input limit.
Source samples show decorative margins, camera/framing changes later in the clip,
and a late close-up. Do not treat the entire edited source as stationary footage.

## Bounded local analysis copy

Only the fully decoded first 180 source frames were used. Crop [0,140,720,1000)
removes vertical margins, producing 720x860 without resizing. Coordinates map as
x_original=x_analysis and y_original=y_analysis+140; analysis index i maps to the
original decoded index i. Original timestamps in this prefix were checked against
i/60 before any encoding. No image positions were renumbered to skip missing frames.

The local preparation used OpenCV mp4v then native macOS avconvert with
PresetHighestQuality to a browser-playable H.264 MOV. This is an image-only analysis
copy; the original file is unchanged. Re-encoding can alter candidate pixels and
is part of this experiment. The validated output has 180 frames, 720x860, no FPS
fallbacks, timestamps 0–2.983333s, and 1/60s largest gap. Its SHA256 is
36b9bea5db38130117c8e57900b87ef771ef4610a1c59632e5427ec81e61ffb2.
The copy is named lion-table-first-180.mov; it and the preparation/inspection JSON
remain in the local visualization artifact folder, outside Git. Bitstream hashes
may differ with another encoder/version; labels must not silently transfer to a
new bitstream without checking provenance. Application limits were not expanded.

## Frozen baseline findings

The detector and temporal parameters at 08e4950 were not changed for this footage.
These are runtime observations, not accuracy measurements: there are no manual
ball/contact/rally reference labels for this source yet.

| Search window in analysis pixels | Observed | Tentative | Ambiguous | Searching | Confirmed IDs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Broad play area [0,120,720,760) | 0 | 33 | 23 | 124 | 0 |
| Browser corner-derived [161,326,563,517) | 0 | 7 | 0 | 173 | 0 |

The broad area had candidates on 56 frames, exactly one on 33 frames, and a longest
consecutive single-candidate run of one frame. Three consecutive unique candidate
frames are required to initialize the tracker, so this sequence never confirmed.
Source images include visually near-repeated frames, but the re-encoded analysis
copy has zero pixel-identical adjacent frames. Do not implement exact-duplicate
skipping on the assumption it explains this failure. Bright floor context, blur,
small components, and competing candidates need labeled diagnostics separately.

The browser-derived table window excludes some airborne positions above the table;
it is not the same experiment as the broader offline window. Both fail to confirm
here. Manual search-area control may be needed for different camera viewpoints;
do not equate a table-plane calibration polygon with the complete airborne region.

Camera inspection is uncertain: six sampled comparisons, five supported, one
inconclusive, maximum supported displacement 0.659px vs threshold 5.608px. No
supported comparison exceeded threshold, but the uncertain result still blocks
calibration reuse. It does not certify camera stability or contact coordinates.

## Browser verification and outcome

The prepared MOV loaded in the actual local browser as 720x860 / 3.000s. Manual
corners [211,344], [523,344], [548,499], [176,499] passed geometry validation.
A real upload/spawned tracking job completed with 180 records and no observations;
gap review correctly shows one entirely unobserved interval. This new case exposed
misleading completion copy saying associations were ready even when none existed.
The client now explicitly reports that no observations were confirmed, while
retaining review access and the contact/rally limitation. This changes result
communication only; it does not fix the underlying tracking failure.

Next annotate a small diagnostic subset of this source, then define a fresh
validation protocol before changing initialization, motion evidence, or search
window behavior. Keep the current failures as baseline evidence. Contacts/rallies
remain unimplemented and cannot be inferred from zero observations or direction
changes. Do not describe this recording as successfully tracked.

The final browser run verified the corrected zero-observation message and the
expanded inspection details showing zero associated observations. The MOV loaded
locally, and source stepping/review remained available even with no observations.
Browser warning/error logs were empty. Full-page screenshot proof remains outside
Git. The changed client script passed node --check; no detector/service code was
changed and no new accuracy score or fresh automated-test run is claimed here.
