"""
RL AI YOUTUBER - FILE WATCHER

Monitors two independent folders:
  - OBS recordings        -> copied to recordings/raw/
  - Rocket League replays -> copied to data/replays/

For each new file the watcher:
  1. waits until the file is completely written
  2. copies it (using a temporary .part name) while computing SHA-256
  3. skips it if the same content was already imported
  4. renames the copy to its final name
  5. registers it in the SQLite table "files"

Original files are NEVER modified or deleted.

Run from the project root:
    python -m agents.file_watcher
    python -m agents.file_watcher --scan-existing replays
"""

import argparse
import hashlib
import logging
import queue
import sqlite3
import threading
import time
import uuid
from contextlib import closing
from datetime import datetime
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from config.settings import (
    OBS_RECORDINGS_DIR,
    PROJECT_ROOT,
    RAW_RECORDINGS_DIR,
    REPLAY_EXTENSION,
    REPLAYS_DIR,
    ROCKET_LEAGUE_REPLAYS_DIR,
    VIDEO_EXTENSIONS,
)
from database.db_manager import get_connection, initialize_database


# ============================================================
# SETTINGS
# ============================================================

# A file is considered "finished" when its size stays the same
# for STABLE_CHECKS_REQUIRED consecutive checks.
CHECK_INTERVAL_SECONDS = 5
STABLE_CHECKS_REQUIRED = 3
# Files not modified for this many seconds are considered finished
# immediately (no need to wait for the stability checks).
OLD_FILE_SECONDS = 60

# Maximum time to wait for a single file (a long OBS recording
# can keep growing for hours).
MAX_WAIT_SECONDS = 12 * 60 * 60

# Files are read/copied in chunks of 1 MB (never loaded fully in RAM).
CHUNK_SIZE = 1024 * 1024

# Temporary suffix used while a copy is in progress.
PARTIAL_SUFFIX = ".part"

LOG_DIR = PROJECT_ROOT / "logs"

# Set when the program is shutting down (Ctrl+C).
STOP_EVENT = threading.Event()

logger = logging.getLogger("file_watcher")


# ============================================================
# LOGGING
# ============================================================

def setup_logging():
    """Log both to the console and to logs/file_watcher.log."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        LOG_DIR / "file_watcher.log", encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# ============================================================
# DATABASE HELPERS
# ============================================================

def find_file_by_sha256(sha256):
    """Return (id, original_name) of a file with this hash, or None."""

    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT id, original_name FROM files WHERE sha256 = ?",
            (sha256,),
        ).fetchone()

    return row


def is_already_imported(original_path, file_size):
    """Quick check: same source path and same size already registered."""

    with closing(get_connection()) as connection:
        row = connection.execute(
            "SELECT id FROM files WHERE original_path = ? AND file_size = ?",
            (str(original_path), file_size),
        ).fetchone()

    return row is not None


def insert_file_record(
    file_id,
    original_name,
    file_type,
    original_path,
    stored_path,
    file_size,
    sha256,
):
    """Register an imported file in the 'files' table."""

    imported_at = datetime.now().isoformat(timespec="seconds")

    with closing(get_connection()) as connection:
        with connection:  # commits automatically if no error occurs
            connection.execute(
                """
                INSERT INTO files (
                    id, original_name, file_type, original_path,
                    stored_path, file_size, imported_at, status, sha256
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    original_name,
                    file_type,
                    str(original_path),
                    str(stored_path),
                    file_size,
                    imported_at,
                    "imported",
                    sha256,
                ),
            )


# ============================================================
# FILE FILTERS
# ============================================================

def is_replay_file(path):
    return path.suffix.lower() == REPLAY_EXTENSION


def is_video_file(path):
    return path.suffix.lower() in VIDEO_EXTENSIONS


# ============================================================
# INGESTOR (one per monitored folder)
# ============================================================

class SourceIngestor:
    """
    Handles ONE source folder.

    Detected files are placed in a queue and processed one at a time
    by a dedicated worker thread. This keeps CPU and disk usage low.
    """

    def __init__(self, label, file_type, source_dir, destination_dir, accepts_file):
        self.label = label
        self.file_type = file_type
        self.source_dir = source_dir
        self.destination_dir = destination_dir
        self.accepts_file = accepts_file

        self._queue = queue.Queue()
        self._pending = set()
        self._lock = threading.Lock()
        self._thread = None

    # ---------- public methods ----------

    def start(self):
        self._thread = threading.Thread(
            target=self._worker_loop,
            name=f"worker-{self.label}",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        if self._thread is not None:
            self._thread.join(timeout=10)

    def submit(self, path):
        """Add a file to the queue (ignored if invalid or already queued)."""

        if not self.accepts_file(path):
            return

        key = str(path)

        with self._lock:
            if key in self._pending:
                return
            self._pending.add(key)

        logger.info("[%s] Detected: %s", self.label, path.name)
        self._queue.put(path)

    def scan_existing(self):
        """Queue the files that are already present in the source folder."""

        count = 0

        for path in sorted(self.source_dir.iterdir()):
            if path.is_file() and self.accepts_file(path):
                self.submit(path)
                count += 1

        logger.info("[%s] Existing files queued: %d", self.label, count)

    # ---------- worker ----------

    def _worker_loop(self):
        while not STOP_EVENT.is_set():
            try:
                path = self._queue.get(timeout=1)
            except queue.Empty:
                continue

            try:
                self._process(path)
            except InterruptedError:
                logger.info("[%s] Interrupted: %s", self.label, path.name)
            except Exception:
                # One failing file must never stop the whole watcher.
                logger.exception("[%s] Error while processing %s", self.label, path.name)
            finally:
                with self._lock:
                    self._pending.discard(str(path))

    def _process(self, source_path):
        # 1. Wait until the file is completely written
        if not self._wait_until_stable(source_path):
            logger.warning(
                "[%s] Skipped (file not ready or no longer available): %s",
                self.label,
                source_path.name,
            )
            return

        stat = source_path.stat()

        # 2. Quick duplicate check (avoids re-copying big files)
        if is_already_imported(source_path, stat.st_size):
            logger.info("[%s] Already imported, skipping: %s", self.label, source_path.name)
            return

        # 3. Build a unique destination name
        file_id = f"file_{uuid.uuid4().hex[:12]}"
        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y%m%d_%H%M%S")
        final_path = self.destination_dir / f"{modified}_{file_id}{source_path.suffix.lower()}"

        # 4. Copy to a temporary name while computing the SHA-256
        logger.info("[%s] Copying: %s", self.label, source_path.name)
        sha256, temp_path, copied_bytes = self._copy_with_hash(source_path, final_path)

        # 5. Duplicate content? Then throw the copy away.
        existing = find_file_by_sha256(sha256)
        if existing is not None:
            temp_path.unlink(missing_ok=True)
            logger.info(
                "[%s] Duplicate content (same as %s, '%s'), not imported: %s",
                self.label,
                existing[0],
                existing[1],
                source_path.name,
            )
            return

        # 6. Final rename, then database registration
        temp_path.replace(final_path)

        try:
            insert_file_record(
                file_id=file_id,
                original_name=source_path.name,
                file_type=self.file_type,
                original_path=source_path,
                stored_path=final_path,
                file_size=copied_bytes,
                sha256=sha256,
            )
        except sqlite3.IntegrityError:
            # Same hash inserted by someone else in the meantime.
            final_path.unlink(missing_ok=True)
            logger.info("[%s] Duplicate (database), not imported: %s", self.label, source_path.name)
            return
        except Exception:
            final_path.unlink(missing_ok=True)
            raise

        logger.info("[%s] IMPORTED: %s -> %s", self.label, source_path.name, final_path.name)

    # ---------- stability check ----------

    def _wait_until_stable(self, path):
        """
        Return True when the file size stayed the same for several
        consecutive checks AND the file can be opened for reading.
        """
        try:
            file_stat = path.stat()
        except FileNotFoundError:
            return False

        age_seconds = time.time() - file_stat.st_mtime

        if file_stat.st_size > 0 and age_seconds > OLD_FILE_SECONDS and self._can_open(path):
            return True

        last_size = -1
        stable_count = 0
        waited = 0

        while waited < MAX_WAIT_SECONDS:
            if STOP_EVENT.is_set():
                return False

            try:
                size = path.stat().st_size
            except FileNotFoundError:
                return False

            if size > 0 and size == last_size:
                stable_count += 1
            else:
                stable_count = 0

            last_size = size

            if stable_count >= STABLE_CHECKS_REQUIRED:
                if self._can_open(path):
                    return True
                stable_count = 0

            STOP_EVENT.wait(CHECK_INTERVAL_SECONDS)
            waited += CHECK_INTERVAL_SECONDS

        return False

    @staticmethod
    def _can_open(path):
        try:
            with open(path, "rb") as file:
                file.read(1024)
            return True
        except OSError:
            return False

    # ---------- copy + hash ----------

    def _copy_with_hash(self, source_path, final_path):
        """
        Copy source_path to '<final_path>.part' while computing SHA-256.
        Returns (sha256_hex, temp_path, copied_bytes).
        """

        self.destination_dir.mkdir(parents=True, exist_ok=True)

        temp_path = final_path.with_name(final_path.name + PARTIAL_SUFFIX)
        hasher = hashlib.sha256()
        total = 0

        try:
            with open(source_path, "rb") as source, open(temp_path, "wb") as target:
                while True:
                    if STOP_EVENT.is_set():
                        raise InterruptedError("Shutdown requested")

                    chunk = source.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    hasher.update(chunk)
                    target.write(chunk)
                    total += len(chunk)

            # The source must not have changed while we were copying it.
            if source_path.stat().st_size != total:
                raise RuntimeError("Source file changed during copy")

        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise

        return hasher.hexdigest(), temp_path, total


# ============================================================
# WATCHDOG EVENT HANDLER
# ============================================================

class NewFileHandler(FileSystemEventHandler):
    """Sends files created or moved into a folder to its ingestor."""

    def __init__(self, ingestor):
        super().__init__()
        self.ingestor = ingestor

    def on_created(self, event):
        if not event.is_directory:
            self.ingestor.submit(Path(event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self.ingestor.submit(Path(event.dest_path))


# ============================================================
# MAIN
# ============================================================

def cleanup_partial_files(folders):
    """Remove leftover .part files from an interrupted run."""

    for folder in folders:
        if folder.exists():
            for leftover in folder.glob(f"*{PARTIAL_SUFFIX}"):
                leftover.unlink(missing_ok=True)
                logger.info("Removed leftover partial file: %s", leftover.name)


def parse_arguments():
    parser = argparse.ArgumentParser(description="RL AI YOUTUBER - file watcher")

    parser.add_argument(
        "--scan-existing",
        choices=["none", "replays", "obs", "all"],
        default="none",
        help="Also import files already present in the source folders "
        "(default: none, only new files are imported).",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    setup_logging()
    initialize_database()

    replay_ingestor = SourceIngestor(
        label="REPLAY",
        file_type="replay",
        source_dir=ROCKET_LEAGUE_REPLAYS_DIR,
        destination_dir=REPLAYS_DIR,
        accepts_file=is_replay_file,
    )

    obs_ingestor = SourceIngestor(
        label="OBS",
        file_type="recording",
        source_dir=OBS_RECORDINGS_DIR,
        destination_dir=RAW_RECORDINGS_DIR,
        accepts_file=is_video_file,
    )

    ingestors = [replay_ingestor, obs_ingestor]

    # The source folders must exist.
    for ingestor in ingestors:
        if not ingestor.source_dir.exists():
            logger.error("Source folder not found: %s", ingestor.source_dir)
            return

        ingestor.destination_dir.mkdir(parents=True, exist_ok=True)

    cleanup_partial_files([REPLAYS_DIR, RAW_RECORDINGS_DIR])

    # Start the workers, then the folder monitoring.
    for ingestor in ingestors:
        ingestor.start()

    observer = Observer()

    for ingestor in ingestors:
        observer.schedule(
            NewFileHandler(ingestor),
            str(ingestor.source_dir),
            recursive=False,
        )

    observer.start()

    if args.scan_existing in ("replays", "all"):
        replay_ingestor.scan_existing()

    if args.scan_existing in ("obs", "all"):
        obs_ingestor.scan_existing()

    logger.info("Watching OBS folder:    %s", OBS_RECORDINGS_DIR)
    logger.info("Watching replay folder: %s", ROCKET_LEAGUE_REPLAYS_DIR)
    logger.info("Watcher running. Press Ctrl+C to stop.")

    try:
        while not STOP_EVENT.is_set():
            STOP_EVENT.wait(1)
    except KeyboardInterrupt:
        logger.info("Stopping watcher...")
    finally:
        STOP_EVENT.set()
        observer.stop()
        observer.join()

        for ingestor in ingestors:
            ingestor.stop()

        logger.info("Watcher stopped.")


if __name__ == "__main__":
    main()