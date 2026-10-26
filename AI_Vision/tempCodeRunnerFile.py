
import sqlite3
import json
from pathlib import Path

# Keep the database beside this file.
DB_PATH = Path(__file__).resolve().parent / "interview.db"


def get_connection():
    """Create a connection to the SQLite database."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Create the required tables if they do not exist."""

    with get_connection() as connection:

        # Candidate accounts
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # One record per interview session
        connection.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                skills TEXT NOT NULL,
                experience TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                question_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress', 'completed')),
                started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                FOREIGN KEY (user_id)
                    REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # One record per evaluated question
        connection.execute("""
            CREATE TABLE IF NOT EXISTS question_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interview_id TEXT NOT NULL,
                question_number INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                score REAL NOT NULL CHECK (score >= 0 AND score <= 10),
                feedback TEXT NOT NULL,
                strengths TEXT NOT NULL,
                weaknesses TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                UNIQUE (interview_id, question_number),

                FOREIGN KEY (interview_id)
                    REFERENCES interviews(id) ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_interviews_user
            ON interviews(user_id)
        """)

def create_interview(
    interview_id,
    user_id,
    role,
    skills,
    experience,
    difficulty,
    question_type
):
    """Create one interview record."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO interviews (
                id, user_id, role, skills, experience,
                difficulty, question_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interview_id,
                user_id,
                role,
                json.dumps(skills),
                experience,
                difficulty,
                question_type
            )
        )


def save_question_result(
    interview_id,
    question_number,
    question_text,
    answer_text,
    result
):
    """Save one evaluated answer."""

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO question_results (
                interview_id, question_number,
                question_text, answer_text, score,
                feedback, strengths, weaknesses, suggestion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                interview_id,
                question_number,
                question_text,
                answer_text,
                result["score"],
                result["feedback"],
                json.dumps(result["strengths"]),
                json.dumps(result["weaknesses"]),
                result["suggestion"]
            )
        )


def complete_interview(interview_id, user_id):
    """Mark an interview completed for its owner."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE interviews
            SET status = 'completed',
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND user_id = ?
              AND status = 'in_progress'
            """,
            (interview_id, user_id)
        )

        return cursor.rowcount == 1


def get_completed_interviews(user_id):
    """Return completed interviews belonging to one user."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                i.id AS interview_id,
                i.role,
                i.started_at,
                i.completed_at,
                COUNT(q.id) AS question_count,
                AVG(q.score) AS average_score,
                MAX(q.score) AS best_score
            FROM interviews AS i
            LEFT JOIN question_results AS q
                ON q.interview_id = i.id
            WHERE i.user_id = ?
              AND i.status = 'completed'
            GROUP BY i.id
            ORDER BY i.started_at DESC
            """,
            (user_id,)
        ).fetchall()

        return [dict(row) for row in rows]


def get_question_history(user_id):
    """Return question results belonging to one user's interviews."""

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                i.id AS interview_id,
                i.role,
                i.skills,
                q.question_number,
                q.question_text,
                q.answer_text,
                q.score,
                q.feedback,
                q.strengths,
                q.weaknesses,
                q.suggestion,
                q.created_at
            FROM interviews AS i
            JOIN question_results AS q
                ON q.interview_id = i.id
            WHERE i.user_id = ?
            ORDER BY q.created_at DESC, q.id DESC
            """,
            (user_id,)
        ).fetchall()

        results = [dict(row) for row in rows]

        for item in results:
            item["skills"] = json.loads(item["skills"])
            item["strengths"] = json.loads(item["strengths"])
            item["weaknesses"] = json.loads(item["weaknesses"])

        return results


if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully: {DB_PATH}")


