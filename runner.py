#!/usr/bin/env python3
"""
One-shot lineup checker for GitHub Actions.
Runs, sends any new alerts, saves state to notified.json, then exits.
State persists across runs because notified.json is committed back to the repo.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import (
    FOOTBALL_DATA_API_KEY,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    LINEUP_CHECK_START_MINUTES,
    LINEUP_CHECK_STOP_MINUTES,
)
from football_api import FootballAPI
from telegram_bot import TelegramBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

NOTIFIED_FILE = Path(__file__).parent / "notified.json"


# ---------------------------------------------------------------------------
# State helpers — notified.json tracks which match IDs we've already alerted
# ---------------------------------------------------------------------------

def load_notified() -> set[int]:
    """Return the set of match IDs already sent today."""
    if not NOTIFIED_FILE.exists():
        return set()
    try:
        data = json.loads(NOTIFIED_FILE.read_text())
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return set(data.get("entries", {}).get(today, []))
    except Exception as exc:
        log.warning("Could not read notified.json: %s — starting fresh", exc)
        return set()


def save_notified(notified_ids: set[int]):
    """Persist notified match IDs for today; old days are dropped automatically."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Load existing entries so we don't wipe parallel runs
    existing: dict = {}
    if NOTIFIED_FILE.exists():
        try:
            existing = json.loads(NOTIFIED_FILE.read_text()).get("entries", {})
        except Exception:
            pass

    # Keep only today's date key (auto-prune yesterday's data)
    existing = {k: v for k, v in existing.items() if k == today}
    existing[today] = sorted(notified_ids)

    NOTIFIED_FILE.write_text(
        json.dumps(
            {"entries": existing, "updated_at": datetime.now(timezone.utc).isoformat()},
            indent=2,
        )
    )
    log.info("Saved notified.json (%d match ID(s) for %s)", len(notified_ids), today)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate():
    missing = [
        k for k, v in {
            "TELEGRAM_BOT_TOKEN":    TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID":      TELEGRAM_CHAT_ID,
            "FOOTBALL_DATA_API_KEY": FOOTBALL_DATA_API_KEY,
        }.items()
        if not v
    ]
    if missing:
        log.error("Missing required secrets: %s", ", ".join(missing))
        sys.exit(1)


def main():
    validate()

    api      = FootballAPI()
    bot      = TelegramBot()
    today    = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now      = datetime.now(timezone.utc)
    notified = load_notified()

    log.info("=== Run started: %s UTC | already notified: %d ===", now.strftime("%H:%M"), len(notified))

    # One API call fetches all configured leagues at once
    matches = api.get_fixtures(today)
    log.info("Fixtures today: %d", len(matches))

    sent = 0
    for match in matches:
        match_id = match["id"]
        home     = match.get("homeTeam", {}).get("name", "?")
        away     = match.get("awayTeam", {}).get("name", "?")

        # Calculate minutes to kickoff
        try:
            kickoff = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
            minutes = (kickoff - now).total_seconds() / 60
        except Exception:
            continue

        # Skip if outside the check window
        if not (-LINEUP_CHECK_STOP_MINUTES <= minutes <= LINEUP_CHECK_START_MINUTES):
            continue

        # Skip if already notified
        if match_id in notified:
            log.info("  [skip] Already notified: %s vs %s", home, away)
            continue

        log.info("  Checking: %s vs %s (kickoff in %d min)", home, away, int(minutes))
        match_data = api.get_lineups(match_id)

        if match_data:
            fixture = {
                "home_team":          home,
                "away_team":          away,
                "league_name":        api.get_competition_name(match),
                "kickoff_utc":        match["utcDate"],
                "minutes_to_kickoff": int(minutes),
            }
            bot.send_lineup_notification(fixture, match_data)
            notified.add(match_id)
            sent += 1
        else:
            log.info("    No lineup confirmed yet")

    save_notified(notified)
    log.info("=== Done. Alerts sent this run: %d ===", sent)


if __name__ == "__main__":
    main()
