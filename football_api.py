import logging
import requests

API_KEY = "2ba896895be58ae9dd278950abc2a0bf"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

LEAGUES = {
    "71": "Bresil Serie A", "119": "Danemark Superliga",
    "244": "Finlande Veikkausliiga", "164": "Islande Urvalsdeild",
    "103": "Norvege Eliteserien", "113": "Suede Allsvenskan",
    "253": "MLS", "61": "Ligue 1", "135": "Serie A",
    "78": "Bundesliga", "94": "Primeira Liga", "88": "Eredivisie",
    "283": "Roumanie Liga I", "106": "Pologne Ekstraklasa",
    "140": "Espagne La Liga",
}

class FootballAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def get_fixtures(self, date):
        matches = []
        for league_id, league_name in LEAGUES.items():
            try:
                resp = self.session.get(f"{BASE_URL}/fixtures", params={"league": league_id, "season": "2026", "date": date}, timeout=10)
                if resp.status_code == 200:
                    for m in resp.json().get("response", []):
                        matches.append({
                            "id": m["fixture"]["id"],
                            "homeTeam": {"name": m["teams"]["home"]["name"]},
                            "awayTeam": {"name": m["teams"]["away"]["name"]},
                            "utcDate": m["fixture"]["date"],
                            "competition": {"name": league_name},
                        })
            except:
                continue
        logging.info(f"API-Football -> {len(matches)} match(s) on {date}")
        return matches

    def get_lineups(self, match_id):
        try:
            resp = self.session.get(f"{BASE_URL}/fixtures", params={"id": match_id}, timeout=10)
            if resp.status_code == 200 and resp.json().get("response"):
                m = resp.json()["response"][0]
                lineups_data = {"home": {"players": []}, "away": {"players": []}}
                for team in m.get("lineups", []):
                    side = "home" if team["team"]["name"] == m["teams"]["home"]["name"] else "away"
                    for p in team.get("startXI", []):
                        lineups_data[side]["players"].append({"player": {"name": p["player"]["name"]}, "starting": True})
                if lineups_data["home"]["players"] and lineups_data["away"]["players"]:
                    return lineups_data
        except:
            pass
        return None

    def get_competition_name(self, match):
        return match.get("competition", {}).get("name", "?")
