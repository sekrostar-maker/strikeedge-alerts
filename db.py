import sqlite3
import logging
from datetime import datetime, timezone
from config import DB_PATH, LINEUP_CHECK_START_MINUTES, LINEUP_CHECK_STOP_MINUTES


class Database:
    def __init__(self):
        self.path = DB_PATH
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_schema(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS fixtures (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_fixture_id     INTEGER UNIQUE NOT NULL,
                    league_id          INTEGER NOT NULL,
                    league_name        TEXT    NOT NULL,
                    home_team          TEXT    NOT NULL,
                    away_team          TEXT    NOT NULL,
                    kickoff_utc        TEXT    NOT NULL,
                    status             TEXT    DEFAULT 'TIMED',
                    lineup_notified    INTEGER DEFAULT 0,
                    date_fetched       TEXT    NOT NULL,
                    updated_at         TEXT    DEFAULT CURRENT_TIMESTAMP
                );
            """)
        logging.info("Database ready at %s", self.path)

    def upsert_fixture(self, fixture: dict):
        """
        Insert or update a normalised fixture dict with keys:
          id, league_id, league_name, home_team, away_team, kickoff_utc, status
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO fixtures
                    (api_fixture_id, league_id, league_name, home_team, away_team,
                     kickoff_utc, status, date_fetched)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(api_fixture_id) DO UPDATE SET
                    status     = excluded.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    fixture["id"],
                    fixture.get("league_id", 0),
                    fixture["league_name"],
                    fixture["home_team"],
                    fixture["away_team"],
                    fixture["kickoff_utc"],
                    fixture["status"],
                    today,
                ),
            )

    def get_fixtures_needing_lineup_check(self) -> list[dict]:
        """
        Return fixtures whose kickoff falls within the check window and whose
        lineups have not yet been notified.
        football-data.org statuses: TIMED, SCHEDULED, IN_PLAY, PAUSED
        """
        now = datetime.now(timezone.utc)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM fixtures
                WHERE lineup_notified = 0
                  AND status IN ('TIMED', 'SCHEDULED', 'IN_PLAY', 'PAUSED')
                ORDER BY kickoff_utc ASC
                """
            ).fetchall()

        result = []
        for row in rows:
            row = dict(row)
            try:
                kickoff = datetime.fromisoformat(row["kickoff_utc"].replace("Z", "+00:00"))
                minutes_to_kickoff = (kickoff - now).total_seconds() / 60
                if -LINEUP_CHECK_STOP_MINUTES <= minutes_to_kickoff <= LINEUP_CHECK_START_MINUTES:
                    row["minutes_to_kickoff"] = int(minutes_to_kickoff)
                    result.append(row)
            except Exception as exc:
                logging.warning("Could not parse kickoff for fixture %s: %s", row.get("api_fixture_id"), exc)
        return result

    def mark_lineup_notified(self, fixture_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE fixtures SET lineup_notified = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (fixture_id,),
            )
