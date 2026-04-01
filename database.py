import sqlite3
from datetime import datetime
from typing import Optional

class Database:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    score_type TEXT NOT NULL DEFAULT 'high',
                    -- high: 數字高勝  low: 數字低勝
                    -- time_short: 時間短勝  time_long: 時間長勝
                    created_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    game_id INTEGER NOT NULL,
                    season INTEGER NOT NULL DEFAULT 1,
                    points INTEGER NOT NULL,
                    note TEXT,
                    recorded_by TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (game_id) REFERENCES games(id)
                );

                CREATE TABLE IF NOT EXISTS seasons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    game_id INTEGER NOT NULL,
                    season INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(guild_id, game_id)
                );

                -- 預設遊戲
                INSERT OR IGNORE INTO games (name, display_name, score_type) VALUES
                    ('darts', '🎯 打標', 'high'),
                    ('pool', '🎱 撞球', 'high'),
                    ('poker', '🃏 撲克', 'high'),
                    ('mahjong', '🀄 麻將', 'high');
            """)
            conn.commit()

    # ── Games ────────────────────────────────────────────────

    def get_games(self):
        with self._conn() as conn:
            return conn.execute("SELECT id, name, display_name, score_type FROM games ORDER BY id").fetchall()

    def get_game(self, name: str):
        with self._conn() as conn:
            return conn.execute(
                "SELECT id, name, display_name, score_type FROM games WHERE name = ?", (name.lower(),)
            ).fetchone()

    def add_game(self, name: str, display_name: str, score_type: str = "high"):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO games (name, display_name, score_type) VALUES (?, ?, ?)",
                (name.lower(), display_name, score_type)
            )
            conn.commit()

    # ── Season ───────────────────────────────────────────────

    def get_season(self, guild_id: str, game_id: int) -> int:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT season FROM seasons WHERE guild_id = ? AND game_id = ?",
                (guild_id, game_id)
            ).fetchone()
            return row[0] if row else 1

    def next_season(self, guild_id: str, game_id: int) -> int:
        with self._conn() as conn:
            current = self.get_season(guild_id, game_id)
            new_season = current + 1
            conn.execute("""
                INSERT INTO seasons (guild_id, game_id, season)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id, game_id) DO UPDATE SET season = excluded.season
            """, (guild_id, game_id, new_season))
            conn.commit()
            return new_season

    # ── Scores ───────────────────────────────────────────────

    def add_score(self, guild_id: str, user_id: str, user_name: str,
                  game_id: int, points: int, note: Optional[str], recorded_by: str):
        season = self.get_season(guild_id, game_id)
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO scores (guild_id, user_id, user_name, game_id, season, points, note, recorded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, user_id, user_name, game_id, season, points, note, recorded_by))
            conn.commit()

    def get_leaderboard(self, guild_id: str, game_id: int, score_type: str, limit: int = 10):
        season = self.get_season(guild_id, game_id)
        order = "ASC" if score_type in ("low", "time_short") else "DESC"
        with self._conn() as conn:
            return conn.execute(f"""
                SELECT user_name, SUM(points) as total, COUNT(*) as rounds
                FROM scores
                WHERE guild_id = ? AND game_id = ? AND season = ?
                GROUP BY user_id
                ORDER BY total {order}
                LIMIT ?
            """, (guild_id, game_id, season, limit)).fetchall()

    def get_history(self, guild_id: str, user_id: str, game_id: int, limit: int = 10):
        season = self.get_season(guild_id, game_id)
        with self._conn() as conn:
            return conn.execute("""
                SELECT points, note, recorded_by, created_at
                FROM scores
                WHERE guild_id = ? AND user_id = ? AND game_id = ? AND season = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (guild_id, user_id, game_id, season, limit)).fetchall()

    def get_user_total(self, guild_id: str, user_id: str, game_id: int) -> int:
        season = self.get_season(guild_id, game_id)
        with self._conn() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(points), 0)
                FROM scores
                WHERE guild_id = ? AND user_id = ? AND game_id = ? AND season = ?
            """, (guild_id, user_id, game_id, season)).fetchone()
            return row[0] if row else 0

    def delete_last_score(self, guild_id: str, user_id: str, game_id: int) -> bool:
        season = self.get_season(guild_id, game_id)
        with self._conn() as conn:
            row = conn.execute("""
                SELECT id FROM scores
                WHERE guild_id = ? AND user_id = ? AND game_id = ? AND season = ?
                ORDER BY created_at DESC LIMIT 1
            """, (guild_id, user_id, game_id, season)).fetchone()
            if not row:
                return False
            conn.execute("DELETE FROM scores WHERE id = ?", (row[0],))
            conn.commit()
            return True
