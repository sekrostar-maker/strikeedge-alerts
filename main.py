#!/usr/bin/env python3
"""
Football Lineup Alert Bot
Polls football-data.org every 20 minutes for lineup announcements
and sends Telegram notifications for configured leagues.
"""

import logging
import sys
import time
from datetime import datetime, timezone

import schedule

from config import (
    FOOTBALL_DATA_API_KEY,
    COMPETITIONS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from db import Database
from football_api import FootballAPI
from telegram_bot import TelegramBot
from mismatch_engine import MismatchAnalyzer
from alert_sender import envoyer_alertes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)


def validate_config():
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_CHAT_ID:
        missing.append("TELEGRAM_CHAT_ID")
    if not FOOTBALL_DATA_API_KEY:
        missing.append("FOOTBALL_DATA_API_KEY")
    if missing:
        log.error("Missing required environment variables: %s", ", ".join(missing))
        log.error("Set them in the Replit Secrets panel and restart.")
        sys.exit(1)


def fetch_today_fixtures(db: Database, api: FootballAPI):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log.info("=== Fetching fixtures for %s ===", today)

    matches = api.get_fixtures(today)
    if not matches:
        log.info("No fixtures found today across configured leagues")
        return

    for match in matches:
        league_name = api.get_competition_name(match)
        db.upsert_fixture({
            "id":           match["id"],
            "league_id":    match.get("competition", {}).get("id", 0),
            "league_name":  league_name,
            "home_team":    match.get("homeTeam", {}).get("name", "Unknown"),
            "away_team":    match.get("awayTeam", {}).get("name", "Unknown"),
            "kickoff_utc":  match.get("utcDate", ""),
            "status":       match.get("status", "TIMED"),
        })

    # Log summary by league
    from collections import Counter
    by_league = Counter(api.get_competition_name(m) for m in matches)
    for league, count in sorted(by_league.items()):
        log.info("  %-22s → %d fixture(s)", league, count)
    log.info("Total: %d fixture(s) stored", len(matches))


def check_lineups(db: Database, api: FootballAPI, bot: TelegramBot):
    pending = db.get_fixtures_needing_lineup_check()
    if not pending:
        log.info("No fixtures in lineup-check window right now")
        return

    log.info("Checking lineups for %d fixture(s) …", len(pending))
    for fixture in pending:
        home = fixture["home_team"]
        away = fixture["away_team"]
        mins = fixture.get("minutes_to_kickoff", "?")
        try:
            match_data = api.get_lineups(fixture["api_fixture_id"])
            if match_data:
                log.info("  Lineups confirmed: %s vs %s — sending alert", home, away)
                try:
                    analyzer = MismatchAnalyzer()
                    lineups_dict = {"domicile": [], "exterieur": []}
                    for p in match_data.get("home", {}).get("players", []):
                        if p.get("starting"): lineups_dict["domicile"].append(p.get("player", {}).get("name", ""))
                    for p in match_data.get("away", {}).get("players", []):
                        if p.get("starting"): lineups_dict["exterieur"].append(p.get("player", {}).get("name", ""))
                    alertes = analyzer.analyser_match(
                        {"domicile": home, "exterieur": away, "heure": fixture.get("kickoff_utc",""), "championnat": fixture.get("league_name","")},
                        lineups_dict
                    )
                    if alertes:
                        envoyer_alertes(
                            {"domicile": home, "exterieur": away, "heure": fixture.get("kickoff_utc",""), "championnat": fixture.get("league_name","")},
                            alertes
                        )
                except Exception as e:
                    log.error("Erreur mismatch: %s", e)
                db.mark_lineup_notified(fixture["id"])
            else:
                log.info("  No lineup yet: %s vs %s (kickoff in %s min)", home, away, mins)
        except Exception as exc:
            log.error("Error checking lineup for %s vs %s: %s", home, away, exc)


def main():
    validate_config()

    db  = Database()
    api = FootballAPI()
    bot = TelegramBot()

    log.info("⚽ Football Lineup Alert Bot is running (football-data.org)")
    log.info("Monitoring %d competitions: %s", len(COMPETITIONS), ", ".join(COMPETITIONS))

    # Run immediately on startup
    fetch_today_fixtures(db, api)
    check_lineups(db, api, bot)

    # Refresh fixture list twice daily (one API call covers all leagues at once)
    schedule.every().day.at("06:00").do(fetch_today_fixtures, db, api)
    schedule.every().day.at("12:00").do(fetch_today_fixtures, db, api)

    # Check lineups every 20 minutes
    schedule.every(20).minutes.do(check_lineups, db, api, bot)

    log.info("Scheduler running — lineup checks every 20 min, fixture refresh at 06:00 & 12:00 UTC")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
