"""Run with python -m backend.inspect_video /path/to/video.mp4."""
import argparse
import json
from pathlib import Path

from backend.adapters.video_reader import VideoError, inspect_video


def main():
    parser = argparse.ArgumentParser(description="Inspect a bounded local table tennis video.")
    parser.add_argument("video", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_video(args.video)
    except VideoError as error:
        parser.exit(1, f"Video rejected: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
