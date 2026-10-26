"""Spawned local inspection and optional experimental tracking entry point."""
import logging
from pathlib import Path
from queue import Full

from backend.adapters.video_reader import VideoError, inspect_video
from backend.adapters.ball_tracking import TrackingRun


class InspectionCancelled(Exception):
    pass


def inspect_worker(video_path: str, cancel_event, messages, options: dict | None = None) -> None:
    def report_frame(count: int, timestamp: float) -> None:
        if cancel_event.is_set():
            raise InspectionCancelled()
        if count == 1 or count % 12 == 0:
            try:
                messages.put_nowait({"kind": "progress", "decoded_frames": count,
                                     "timestamp_seconds": timestamp})
            except Full:
                # Progress is replaceable; never stall decoding on a slow poller.
                pass

    try:
        if cancel_event.is_set():
            raise InspectionCancelled()
        tracking = TrackingRun(tuple(options["search_region"])) if options and options["mode"] == "track" else None
        result = inspect_video(Path(video_path), on_frame=report_frame,
                               frame_processor=tracking.consume if tracking else None)
        if tracking is not None:
            result["tracking"] = tracking.result()
        messages.put({"kind": "completed", "result": result}, timeout=2)
    except InspectionCancelled:
        messages.put({"kind": "cancelled"}, timeout=2)
    except VideoError as error:
        messages.put({"kind": "failed", "error": str(error)}, timeout=2)
    except Exception:
        logging.exception("Unexpected inspection worker failure")
        messages.put({"kind": "failed", "error": "Video inspection failed."}, timeout=2)
