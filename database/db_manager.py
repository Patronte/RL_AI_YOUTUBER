
import sqlite3
from pathlib import Path

from config.settings import DATABASE_PATH


def get_connection():
    """
    Create and return a connection to the SQLite database.
    """

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def initialize_database():
    """
    Create the database tables if they do not already exist.
    """

    with get_connection() as connection:

        # ----------------------------------------------------
        # FILES TABLE
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                original_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                original_path TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                imported_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'imported',
                sha256 TEXT UNIQUE
            )
        """)

        # ----------------------------------------------------
        # MATCHES TABLE
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                replay_file_id TEXT,
                recording_file_id TEXT,
                match_date TEXT,
                playlist TEXT,
                blue_score INTEGER,
                orange_score INTEGER,
                analysis_status TEXT DEFAULT 'pending',

                FOREIGN KEY (replay_file_id)
                    REFERENCES files(id),

                FOREIGN KEY (recording_file_id)
                    REFERENCES files(id)
            )
        """)

        # ----------------------------------------------------
        # HIGHLIGHTS TABLE
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS highlights (
                id TEXT PRIMARY KEY,
                match_id TEXT,
                start_time REAL,
                end_time REAL,
                category TEXT,
                score REAL,
                video_path TEXT,
                status TEXT DEFAULT 'pending',

                FOREIGN KEY (match_id)
                    REFERENCES matches(id)
            )
        """)

        # ----------------------------------------------------
        # CONTENT TABLE
        # ----------------------------------------------------

        connection.execute("""
            CREATE TABLE IF NOT EXISTS content (
                id TEXT PRIMARY KEY,
                highlight_id TEXT,
                title TEXT,
                description TEXT,
                content_type TEXT,
                video_path TEXT,
                approval_status TEXT DEFAULT 'pending',
                publishing_status TEXT DEFAULT 'not_published',

                FOREIGN KEY (highlight_id)
                    REFERENCES highlights(id)
            )
        """)

    print("[OK] Database initialized successfully.")
    print(f"[OK] Database location: {DATABASE_PATH}")


def list_tables():
    """
    Display all tables currently stored in the database.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
        """)

        tables = cursor.fetchall()

    print("\nDatabase tables:")

    for table in tables:
        print(f"- {table[0]}")


if __name__ == "__main__":

    print("=" * 60)
    print("RL AI YOUTUBER - DATABASE MANAGER")
    print("=" * 60)

    initialize_database()
    list_tables()
