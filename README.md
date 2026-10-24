# Sports Replay Analyst

Local table tennis replay analysis, built incrementally with Python, OpenCV,
FastAPI, Jinja2, and plain browser JavaScript.

## Current stage

The application shell is implemented. Ball tracking, table-contact estimation,
rally timing, and uploads are not implemented. No analysis results are fabricated.

## Run locally

Use Python 3.12. Install dependencies in this project's own environment:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Do not expose this development server publicly.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Only frontend static files are public. Videos, extracted frames, weights, and
local environments must remain untracked. The first version targets one fixed
camera and a visible table surface, with manually selected table corners.
Image-space motion is not a 3D trajectory. An airborne ball cannot be mapped to
its true table coordinates using a table-plane homography.

The supplied preview clip has a watermark, overhead perspective, blur, and
apparent camera drift. It has not been validated for contact or rally accuracy.
See AGENTS.md for stage boundaries and the master/develop workflow.
