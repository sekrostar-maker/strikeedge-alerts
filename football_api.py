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

    def get_team_stats(self, team_name, league_id):
        """Stats complètes d'une équipe dans un championnat"""
        try:
            resp = self.session.get(f"{BASE_URL}/teams", params={"search": team_name}, timeout=10)
            if resp.status_code == 200:
                for t in resp.json().get("response", []):
                    if t["team"]["name"] == team_name:
                        tid = t["team"]["id"]
                        r2 = self.session.get(f"{BASE_URL}/teams/statistics", params={"team": tid, "league": league_id, "season": "2026"}, timeout=10)
                        if r2.status_code == 200:
                            d = r2.json().get("response", {})
                            return {
                                "matchs": d.get("fixtures", {}).get("played", {}).get("total", 0) or 0,
                                "buts_marques": d.get("goals", {}).get("for", {}).get("total", {}).get("total", 0) or 0,
                                "buts_encaisses": d.get("goals", {}).get("against", {}).get("total", {}).get("total", 0) or 0,
                                "clean_sheets": d.get("clean_sheet", {}).get("total", 0) or 0,
                            }
        except:
            pass
        return None

    def get_h2h_teams(self, team1, team2):
        """Historique des confrontations entre 2 équipes"""
        try:
            resp = self.session.get(f"{BASE_URL}/fixtures/headtohead", params={"h2h": f"{team1}-{team2}"}, timeout=10)
            if resp.status_code == 200:
                matches = resp.json().get("response", [])
                h2h = {"total": len(matches), "buts_team1": 0, "buts_team2": 0}
                for m in matches:
                    h2h["buts_team1"] += m["goals"]["home"] if m["teams"]["home"]["name"] == team1 else m["goals"]["away"]
                    h2h["buts_team2"] += m["goals"]["away"] if m["teams"]["home"]["name"] == team1 else m["goals"]["home"]
                return h2h
        except:
            pass
        return None

    def get_absences(self, team_name):
        """Blessés et suspendus"""
        try:
            resp = self.session.get(f"{BASE_URL}/players/seasons", params={"team": team_name}, timeout=10)
            if resp.status_code == 200:
                absences = []
                for p in resp.json().get("response", []):
                    if p.get("player", {}).get("injured"):
                        absences.append(p["player"]["name"])
                return absences[:5]
        except:
            pass
        return []

    def get_player_detailed_stats(self, player_name, team_name):
        """Stats détaillées: buts par type, fautes subies, cartons, passes"""
        try:
            resp = self.session.get(f"{BASE_URL}/players", params={"search": player_name, "season": "2026"}, timeout=10)
            if resp.status_code == 200:
                for p in resp.json().get("response", []):
                    for s in p.get("statistics", []):
                        if s.get("team", {}).get("name") == team_name:
                            return {
                                "buts_total": s.get("goals", {}).get("total", 0) or 0,
                                "buts_tete": s.get("goals", {}).get("head", 0) or 0,
                                "buts_pied": s.get("goals", {}).get("left", 0) or 0 + (s.get("goals", {}).get("right", 0) or 0),
                                "buts_penalty": s.get("goals", {}).get("penalty", 0) or 0,
                                "passes_cles": s.get("passes", {}).get("key", 0) or 0,
                                "fautes_subies": s.get("fouls", {}).get("drawn", 0) or 0,
                                "cartons_jaunes": s.get("cards", {}).get("yellow", 0) or 0,
                                "cartons_rouges": s.get("cards", {}).get("red", 0) or 0,
                                "matchs": s.get("games", {}).get("appearences", 0) or 0,
                                "minutes": s.get("games", {}).get("minutes", 0) or 0,
                                "xg": s.get("xg", {}).get("total", 0) or 0,
                            }
        except:
            pass
        return None
