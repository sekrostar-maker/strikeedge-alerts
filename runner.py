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
            
            if not (-120 <= minutes <= 120):
                continue
            
            if mid in MATCHS_ANALYSES:
                continue
            
            log.info("  %s vs %s (%.0f min)", home, away, minutes)
            MATCHS_ANALYSES.add(mid)
            competition_name = api.get_competition_name(match)

            # Si championnat nordique -> Claude DIRECTEMENT
            if competition_name in NORDIC_LEAGUES:
                log.info("    Appel Claude pour %s vs %s", home, away)
                claude_result = analyze_nordic_match(match)
                if claude_result and 'error' not in claude_result:
                    alertes = engine._parse_claude_result(claude_result)
                    if alertes:
                        envoyer_alertes({'domicile':home,'exterieur':away,'heure':match.get('utcDate','?'),'championnat':competition_name}, alertes)
                        log.info("    ALERTE CLAUDE envoyee")
                else:
                    log.error("    Claude error: %s", str(claude_result)[:200])
            else:
                # Sinon -> Groq/Fallback
                try:
                    alertes_sans = engine.analyse_match_sans_lineups(match)
                    if alertes_sans:
                        envoyer_alertes({'domicile':home,'exterieur':away,'heure':match.get('utcDate','?'),'championnat':competition_name}, alertes_sans)
                        log.info("    ALERTE envoyee")
                        for a in alertes_sans:
                            brain.save_prediction(mid, f"{home} vs {away}", a['type'], a['probabilite'])
                except Exception as e:
                    log.error("    Erreur: %s", e)

        save_notified(notified)
        if cycle < 7:
            time.sleep(120)
    
    log.info("=== Done ===")

if __name__ == "__main__":
    main()
