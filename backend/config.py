from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIRECTORY = PROJECT_ROOT / "frontend" / "static"
TEMPLATE_DIRECTORY = PROJECT_ROOT / "frontend" / "templates"
MAX_VIDEO_BYTES = 100 * 1024 * 1024
MAX_DURATION_SECONDS = 60
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
MAX_FPS = 120
