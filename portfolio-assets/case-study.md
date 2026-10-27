# Sports Replay Analyst — three-page portfolio copy

Use one large image, one short heading and a compact explanation per page.
Keep the navy/cyan palette and the concept/experimental image captions.
This is the concise format requested by the project owner.

## Page 1 — Project overview

Image: sports-replay-purpose-cover-v2.png

### Sports Replay Analyst

Table Tennis Video Analysis

Sports Replay Analyst is a local video analysis prototype for table tennis. It
combines frame-by-frame replay, manual table calibration, and experimental ball
tracking to help users inspect the ball’s movement and review missing observations.

- My role: Full-stack & computer vision development
- Stack: Python · OpenCV · FastAPI · JavaScript
- Platform: Local web application

## Page 2 — Workflow

Image: sports-replay-workflow-v2.png

### From Video to Ball Observations

Users load a recorded clip, mark the table corners, and run local analysis.
OpenCV extracts ball candidates, while a temporal tracker associates observations
across frames. Playback controls and gap review help users inspect where tracking
succeeds or loses evidence.

- Candidate detection: Identify possible ball positions.
- 2D tracking: Display associated observations with visible gaps.
- Frame review: Inspect individual frames and unobserved intervals.

## Page 3 — Technical approach

Image: sports-replay-labeling-v2.png

### Reviewed Data. Testable Logic.

The project separates video decoding, candidate detection, tracking rules, and
presentation. A manual annotation workspace supports bounding-box review and
YOLO dataset export. Recording-based split checks help prevent related frames
from entering both training and validation sets.

Local PyTorch and YOLO experiments support detector development. Automated tests
cover tracking rules, source coordinates, worker cleanup, and dataset integrity.

Status: Working replay prototype with experimental ball tracking. Neural detector
development is ongoing.

Suggested links: View Source Code · Watch Demo
