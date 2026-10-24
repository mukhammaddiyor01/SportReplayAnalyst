# Video inspection evidence

The user-provided preview was decoded locally using the project Python 3.12
environment and OpenCV. No frames or video bytes were committed or sent out.

- Decoded frames: 360; source dimensions: 768 x 432.
- First timestamp: 0 seconds; last frame timestamp: 11.978633333333335 seconds.
- Largest consecutive timestamp gap: 0.03336666666666943 seconds.
- FPS fallback frames: 0.
- Earlier container inspection: approximately 29.970 FPS, 12.012-second duration.

These checks verify decoding and timestamp continuity only. They do not measure
ball detection, track quality, contact recognition, camera stability, or rallies.
Sampled images show overhead perspective, watermark, ball blur, and apparent
camera drift. No held-out manually annotated evaluation exists yet.

Automated checks cover source coordinates/timing, missing/empty/corrupt media,
byte/dimension/FPS/duration limits, and explicit missing-timestamp fallback.
