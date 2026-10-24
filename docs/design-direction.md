# Replay workspace design

## Direction

A focused replay desk for preparing table tennis footage. The video is the
primary surface; the calibration inspector is its attached tool, not a dashboard.
Use a compact product header and an understated page title rather than a hero.

Palette: canvas #f3f6f8, white #ffffff, ink #243746, slate #637784,
replay blue #183d51, and geometry amber #ffb469.
Typography: local Avenir Next with Segoe UI fallback. Medium-weight headings,
readable 13–15px controls, tabular numeric timestamps. No external fonts.

```text
[table mark] Sports Replay Analyst                    Local processing
Replay workspace                       Table calibration
[ Video preview                            ][ 1  Video source       ]
[                                          ][    filename / limits  ]
[              replay surface              ][ 2  Table corners 0/4 ]
[                                          ][    coordinates       ]
[ play    ━━━━━━━ time                      ][    Check calibration ]
[ Frame calibration note                   ][    status             ]
```

The table diagram belongs only to the clearly labelled empty state. It suggests
which surface to mark and never pretends to be a video or analysis result.
Numbering encodes the actual preparation sequence. The amber highlight is
reserved for geometry. Dark playback chrome separates transport from setup.

## Review of the earlier layout

Removed the oversized opening headline, duplicate-looking file controls, long
technical paragraphs, and undifferentiated button row. Revised the generic
video-plus-text block into a replay surface and a compact inspector, with status
separate from instructions. Keep limits discoverable and local processing clear.
Use a single prominent calibration action and quieter Undo/Remove controls.

## Interaction requirements

Retain all existing IDs and source-coordinate behavior. Show actual corner count,
filename, metadata, and calibration status. Clear geometry on playback or seeking.
Provide numeric inputs and visible keyboard focus. Stack the inspector beneath
the preview on narrow screens; never crop the source video or distort the canvas.
No invented analytics, unavailable analysis actions, or autoplay motion.
