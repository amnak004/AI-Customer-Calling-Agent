
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "data" / "database"
DB_FILE = DB_DIR / "quickcart.db"


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                intent TEXT,
                source TEXT,
                provider TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                success INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)


def save_conversation(
    customer_message,
    bot_response,
    intent=None,
    source=None,
    provider=None,
    input_tokens=0,
    output_tokens=0
):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO conversations (
                customer_message,
                bot_response,
                intent,
                source,
                provider,
                input_tokens,
                output_tokens,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_message,
            bot_response,
            intent,
            source,
            provider,
            input_tokens,
            output_tokens,
            datetime.now(timezone.utc).isoformat()
        ))


def get_conversations(limit=50):
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM conversations
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


def save_api_usage(
    provider,
    input_tokens=0,
    output_tokens=0,
    success=True
):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO api_usage (
                provider,
                input_tokens,
                output_tokens,
                success,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            provider,
            input_tokens,
            output_tokens,
            int(success),
            datetime.now(timezone.utc).isoformat()
        ))


def get_api_usage():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT provider,
                   SUM(input_tokens) AS total_input_tokens,
                   SUM(output_tokens) AS total_output_tokens,
                   COUNT(*) AS total_requests
            FROM api_usage
            GROUP BY provider
        """).fetchall()

        return [dict(row) for row in rows]


# Initialize tables when this module loads
initialize_database()
