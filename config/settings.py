
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

# settings.py is inside config/
# Its parent directory is the project root.

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# EXTERNAL SOURCE DIRECTORIES
# ============================================================

# OBS recordings
OBS_RECORDINGS_DIR = Path(
    r"C:\Users\kazam\Videos\Rocket Video"
)

# Rocket League saved replays
ROCKET_LEAGUE_REPLAYS_DIR = Path(
    r"C:\Users\kazam\Documents\My Games\Rocket League\TAGame\DemosEpic"
)


# ============================================================
# PROJECT DIRECTORIES
# ============================================================

CONFIG_DIR = PROJECT_ROOT / "config"
DATABASE_DIR = PROJECT_ROOT / "database"
AGENTS_DIR = PROJECT_ROOT / "agents"
RENDERING_DIR = PROJECT_ROOT / "rendering"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

DATA_DIR = PROJECT_ROOT / "data"
REPLAYS_DIR = DATA_DIR / "replays"
PARSED_DIR = DATA_DIR / "parsed"
MATCHES_DIR = DATA_DIR / "matches"
ANALYTICS_DIR = DATA_DIR / "analytics"

RECORDINGS_DIR = PROJECT_ROOT / "recordings"
RAW_RECORDINGS_DIR = RECORDINGS_DIR / "raw"
HIGHLIGHTS_DIR = RECORDINGS_DIR / "highlights"
TEMPORARY_DIR = RECORDINGS_DIR / "temporary"

OUTPUT_DIR = PROJECT_ROOT / "output"
SHORTS_DIR = OUTPUT_DIR / "shorts"
LONG_FORM_DIR = OUTPUT_DIR / "long_form"
THUMBNAILS_DIR = OUTPUT_DIR / "thumbnails"
APPROVED_DIR = OUTPUT_DIR / "approved"


# ============================================================
# DATABASE
# ============================================================

DATABASE_PATH = DATABASE_DIR / "rl_ai_youtuber.db"


# ============================================================
# FILE SETTINGS
# ============================================================

REPLAY_EXTENSION = ".replay"

VIDEO_EXTENSIONS = {
    ".mkv",
    ".mp4",
    ".mov",
    ".avi",
}


# ============================================================
# RECORDING SETTINGS
# ============================================================

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 60


# ============================================================
# VALIDATION
# ============================================================

def validate_source_directories():
    """Check whether the external source directories exist."""

    sources = {
        "OBS recordings": OBS_RECORDINGS_DIR,
        "Rocket League replays": ROCKET_LEAGUE_REPLAYS_DIR,
    }

    for name, path in sources.items():
        if path.exists():
            print(f"[OK] {name}: {path}")
        else:
            print(f"[WARNING] {name} directory not found: {path}")


if __name__ == "__main__":
    print("=" * 60)
    print("RL AI YOUTUBER - PROJECT CONFIGURATION")
    print("=" * 60)

    print(f"\nProject root: {PROJECT_ROOT}")
    print(f"Database: {DATABASE_PATH}")

    print("\nExternal source directories:")
    validate_source_directories()
