#!/usr/bin/env python3
"""
One-shot lineup checker for GitHub Actions.
Runs every hour, checks lineups every 2 minutes for 60 minutes.
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, FOOTBALL_DATA_API_KEY
from football_api import FootballAPI
from telegram_bot import TelegramBot
from engine import AnalysisEngine
from alert_sender import envoyer_alertes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

NOTIFIED_FILE = Path(__file__).parent / "notified.json"

def load_notified():
    if not NOTIFIED_FILE.exists():
        return set()
    try:
        data = json.loads(NOTIFIED_FILE.read_text())
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return set(data.get("entries", {}).get(today, []))
    except:
        return set()

def save_notified(notified_ids):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    NOTIFIED_FILE.write_text(json.dumps({"entries": {today: sorted(notified_ids)}, "updated_at": datetime.now(timezone.utc).isoformat()}, indent=2))

def main():
    api = FootballAPI()
    bot = TelegramBot()
    engine = AnalysisEngine()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    notified = load_notified()
    sent = 0

    log.info("=== Run started ===")
    
    for cycle in range(30):  # 30 × 2min = 60min
        now = datetime.now(timezone.utc)
        matches = api.get_fixtures(today)
        log.info("Cycle %d: %d matchs", cycle+1, len(matches))
        
        for match in matches:
            mid = match["id"]
            home = match.get("homeTeam", {}).get("name", "?")
            away = match.get("awayTeam", {}).get("name", "?")
            
            if mid in notified:
                continue
            
            try:
                kickoff = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
                minutes = (kickoff - now).total_seconds() / 60
            except:
                continue
            
            # Analyse sans lineups (stats equipes)
            try:
                alertes_sans = engine.analyse_match_sans_lineups(match)
                if alertes_sans:
                    envoyer_alertes({'domicile':home,'exterieur':away,'heure':match.get('utcDate','?'),'championnat':api.get_competition_name(match)}, alertes_sans)
                    log.info('    ALERTE EQUIPE envoyee')
            except Exception as e:
                pass
            
            if -15 <= minutes <= 120:
                log.info("  %s vs %s (%.0f min)", home, away, minutes)
                match_data = api.get_lineups(mid)
                if match_data:
                    log.info('    Lineups trouvees pour %s vs %s', home, away)
                    # Analyse des mismatches
                    try:
                        alertes = engine.analyse_match(match)
                        if alertes:
                            envoyer_alertes({'domicile':home,'exterieur':away,'heure':match.get('utcDate','?'),'championnat':api.get_competition_name(match)}, alertes)
                            log.info("    ALERTE ENVOYEE: %d recommandations", len(alertes))
                    except Exception as e:
                        log.error("    Erreur analyse: %s", e)
                    
                    fixture = {"home_team": home, "away_team": away, "league_name": api.get_competition_name(match), "kickoff_utc": match["utcDate"], "minutes_to_kickoff": int(minutes)}
                    fixture = {"home_team": home, "away_team": away, "league_name": api.get_competition_name(match), "kickoff_utc": match["utcDate"], "minutes_to_kickoff": int(minutes)}
                    bot.send_lineup_notification(fixture, match_data)
                    notified.add(mid)
                    sent += 1
        
        save_notified(notified)
        
        if cycle < 29:
            time.sleep(120)  # 2 minutes
    
    log.info("=== Done. Alerts sent: %d ===", sent)

if __name__ == "__main__":
    main()
