"""Spawned worker entry point. It only inspects video, never invents tracking."""
import logging
from pathlib import Path
from queue import Full

from backend.adapters.video_reader import VideoError, inspect_video


class InspectionCancelled(Exception):
    pass


def inspect_worker(video_path: str, cancel_event, messages) -> None:
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
        result = inspect_video(Path(video_path), on_frame=report_frame)
        messages.put({"kind": "completed", "result": result}, timeout=2)
    except InspectionCancelled:
        messages.put({"kind": "cancelled"}, timeout=2)
    except VideoError as error:
        messages.put({"kind": "failed", "error": str(error)}, timeout=2)
    except Exception:
        logging.exception("Unexpected inspection worker failure")
        messages.put({"kind": "failed", "error": "Video inspection failed."}, timeout=2)
