
import json
import sqlite3

from pathlib import Path
from datetime import datetime


# 数据库文件放在 backend 目录下
DB_PATH = Path(__file__).resolve().parent / "interview.db"


def get_connection():
    """创建数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库和面试记录表"""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interviews (
                id TEXT PRIMARY KEY,
                resume_text TEXT NOT NULL,
                history TEXT NOT NULL,
                stage TEXT NOT NULL,
                total_turns INTEGER NOT NULL DEFAULT 0,
                completed INTEGER NOT NULL DEFAULT 0,
                summary TEXT,
                started_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_session(session):
    """保存或更新一条面试记录"""

    now = datetime.now().isoformat()

    history_json = json.dumps(
        session.get("history", []),
        ensure_ascii=False
    )

    summary = session.get("summary")

    summary_json = (
        json.dumps(summary, ensure_ascii=False)
        if summary is not None
        else None
    )

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO interviews (
                id,
                resume_text,
                history,
                stage,
                total_turns,
                completed,
                summary,
                started_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(id) DO UPDATE SET
                resume_text = excluded.resume_text,
                history = excluded.history,
                stage = excluded.stage,
                total_turns = excluded.total_turns,
                completed = excluded.completed,
                summary = excluded.summary,
                updated_at = excluded.updated_at
        """, (
            session["session_id"],
            session["resume_text"],
            history_json,
            session["stage"],
            session["total_turns"],
            int(session["completed"]),
            summary_json,
            session["started_at"],
            now
        ))

        conn.commit()


def get_session_from_db(session_id):
    """根据 ID 获取完整面试记录"""

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM interviews WHERE id = ?",
            (session_id,)
        ).fetchone()

    if row is None:
        return None

    session = {
        "session_id": row["id"],
        "resume_text": row["resume_text"],
        "history": json.loads(row["history"]),
        "stage": row["stage"],
        "total_turns": row["total_turns"],
        "completed": bool(row["completed"]),
        "summary": (
            json.loads(row["summary"])
            if row["summary"]
            else None
        ),
        "started_at": row["started_at"]
    }

    return session


def get_all_sessions():
    """获取历史面试列表，不返回完整简历和对话"""

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                id,
                resume_text,
                stage,
                total_turns,
                completed,
                summary,
                started_at,
                updated_at
            FROM interviews
            ORDER BY started_at DESC
        """).fetchall()

    result = []

    for row in rows:
        summary = (
            json.loads(row["summary"])
            if row["summary"]
            else None
        )

        candidate_info = (
            summary.get("candidate_info", {})
            if isinstance(summary, dict)
            else {}
        )

        result.append({
            "session_id": row["id"],
            "candidate_name": candidate_info.get(
                "name", "待识别"
            ),
            "position": "技术实习生",
            "stage": row["stage"],
            "total_turns": row["total_turns"],
            "completed": bool(row["completed"]),
            "has_summary": summary is not None,
            "started_at": row["started_at"],
            "updated_at": row["updated_at"]
        })

    return result


def delete_session_from_db(session_id):
    """删除指定面试记录"""

    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM interviews WHERE id = ?",
            (session_id,)
        )
        conn.commit()

        return cursor.rowcount > 0
