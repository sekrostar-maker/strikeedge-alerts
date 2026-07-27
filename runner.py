import json, logging, sys, time
from datetime import datetime, timezone
from pathlib import Path
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from football_api import FootballAPI
from telegram_bot import TelegramBot
from engine import AnalysisEngine
from brain import Brain
from alert_sender import envoyer_alertes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

NOTIFIED_FILE = Path(__file__).parent / "notified.json"
MATCHS_ANALYSES = set()

def load_notified():
    if not NOTIFIED_FILE.exists(): return set()
    try:
        data = json.loads(NOTIFIED_FILE.read_text())
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return set(data.get("entries", {}).get(today, []))
    except: return set()

def save_notified(ids):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    NOTIFIED_FILE.write_text(json.dumps({"entries": {today: sorted(ids)}}, indent=2))

def main():
    api = FootballAPI()
    bot = TelegramBot()
    engine = AnalysisEngine()
    brain = Brain()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    notified = load_notified()
    sent = 0

    log.info("=== Run started ===")
    
    for cycle in range(8):
        now = datetime.now(timezone.utc)
        matches = api.get_fixtures(today)
        log.info("Cycle %d: %d matchs", cycle+1, len(matches))

        for match in matches:
            mid = match["id"]
            home = match.get("homeTeam", {}).get("name", "?")
            away = match.get("awayTeam", {}).get("name", "?")
            
            try:
                kickoff = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
                minutes = (kickoff - now).total_seconds() / 60
            except:
                continue
            
            # Seulement les matchs entre 2h avant et 15min après
            if not (-15 <= minutes <= 120):
                continue
            
            # Déjà analysé ? on passe
            if mid in MATCHS_ANALYSES:
                continue
            
            log.info("  %s vs %s (%.0f min)", home, away, minutes)
            MATCHS_ANALYSES.add(mid)
            
            # Analyse sans lineups
            try:
                alertes = engine.analyse_match_sans_lineups(match)
                if alertes:
                    envoyer_alertes({'domicile':home,'exterieur':away,'heure':match.get('utcDate','?'),'championnat':api.get_competition_name(match)}, alertes)
                    log.info("    ALERTE envoyee")
                    for a in alertes:
                        brain.save_prediction(mid, f"{home} vs {away}", a['type'], a['probabilite'])
            except Exception as e:
                log.error("    Erreur: %s", e)

        save_notified(notified)
        if cycle < 7:
            time.sleep(120)
    
    log.info("=== Done. Alertes: %d ===", sent)

if __name__ == "__main__":
    main()
