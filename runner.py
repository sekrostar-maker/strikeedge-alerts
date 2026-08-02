import json, logging, sys, time
from datetime import datetime, timezone
from pathlib import Path
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from football_api import FootballAPI
from engine import AnalysisEngine
from claude_nordic_analyzer import analyze_nordic_match, NORDIC_LEAGUES
from brain import Brain
from alert_sender import envoyer_alertes

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)
NOTIFIED_FILE = Path(__file__).parent / "notified.json"
CLAUDE_DONE = set()

def main():
    api = FootballAPI()
    engine = AnalysisEngine()
    brain = Brain()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log.info("=== Run started ===")
    matches = api.get_fixtures(today)
    log.info("%d matchs trouves", len(matches))
    now = datetime.now(timezone.utc)

    for match in matches:
        home = match.get("homeTeam", {}).get("name", "?")
        away = match.get("awayTeam", {}).get("name", "?")
        mid = match["id"]
        competition = api.get_competition_name(match)
        
        if competition not in NORDIC_LEAGUES or mid in CLAUDE_DONE:
            continue
        
        try:
            kickoff = datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00"))
            minutes = (kickoff - now).total_seconds() / 60
        except:
            continue
        
        if not (-15 <= minutes <= 120):
            continue
        
        hs = api.get_team_stats(home, match.get('league_id',''))
        if hs and hs.get('matchs', 0) < 5:
            log.info("  %s vs %s: skipped (<5 matchs)", home, away)
            continue
        
        log.info("  Appel Claude: %s vs %s (%.0f min)", home, away, minutes)
        CLAUDE_DONE.add(mid)
        result = analyze_nordic_match(match)
        
        if result and 'error' not in result:
            alertes = engine._parse_claude_result(result)
            if alertes:
                envoyer_alertes({'domicile':home,'exterieur':away,'heure':match.get('utcDate','?'),'championnat':competition}, alertes)
                log.info("    ALERTE CLAUDE envoyee")
        else:
            log.error("    Claude error: %s", str(result)[:200])
    
    log.info("=== Done ===")

if __name__ == "__main__":
    main()
