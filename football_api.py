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
                        "league_id": league_id,
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
        try:
            resp = self.session.get(f"{BASE_URL}/fixtures/headtohead", params={"h2h": f"{team1}-{team2}"}, timeout=10)
            if resp.status_code == 200:
                matches = resp.json().get("response", [])
                scores = []
                buts_t1 = 0
                buts_t2 = 0
                for m in matches:
                    h = m["teams"]["home"]["name"]
                    a = m["teams"]["away"]["name"]
                    gh = m["goals"]["home"]
                    ga = m["goals"]["away"]
                    scores.append(f"{h} {gh}-{ga} {a}")
                    if h == team1:
                        buts_t1 += gh
                        buts_t2 += ga
                    else:
                        buts_t1 += ga
                        buts_t2 += gh
                return {"total": len(matches), "scores": scores, "buts_team1": buts_t1, "buts_team2": buts_t2}
        except:
            pass
        return None
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

    def get_player_advanced_stats(self, player_name, team_name):
        """Stats avancées: duels aériens %, dribbles %, penalties, passes décisives"""
        try:
            resp = self.session.get(f"{BASE_URL}/players", params={"search": player_name, "season": "2026"}, timeout=10)
            if resp.status_code == 200:
                for p in resp.json().get("response", []):
                    for s in p.get("statistics", []):
                        if s.get("team", {}).get("name") == team_name:
                            duels = s.get("duels", {})
                            dribbles = s.get("dribbles", {})
                            passes = s.get("passes", {})
                            return {
                                "duels_aeriens_gagnes": duels.get("won", 0) or 0,
                                "duels_aeriens_total": duels.get("total", 0) or 0,
                                "dribbles_reussis": dribbles.get("success", 0) or 0,
                                "dribbles_tentatives": dribbles.get("attempts", 0) or 0,
                                "passes_decisives": passes.get("assists", 0) or 0,
                                "penalties_marques": s.get("penalty", {}).get("scored", 0) or 0,
                                "penalties_tentes": s.get("penalty", {}).get("total", 0) or 0,
                            }
        except:
            pass
        return None

    def get_team_xg(self, team_name, league_id):
        """xG pour et contre d'une équipe"""
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
                                "xg_pour": d.get("xg", {}).get("for", {}).get("total", 0) or 0,
                                "xg_contre": d.get("xg", {}).get("against", {}).get("total", 0) or 0,
                            }
        except:
            pass
        return None

    def get_team_form(self, team_name, league_id, nb=5):
        """Forme récente depuis les stats de l'équipe"""
        try:
            resp = self.session.get(f"{BASE_URL}/teams", params={"search": team_name}, timeout=10)
            if resp.status_code == 200:
                for t in resp.json().get("response", []):
                    if t["team"]["name"] == team_name:
                        tid = t["team"]["id"]
                        r2 = self.session.get(f"{BASE_URL}/teams/statistics", params={"team": tid, "league": league_id, "season": "2026"}, timeout=10)
                        if r2.status_code == 200:
                            d = r2.json().get("response", {})
                            form = d.get("form", "")
                            goals = d.get("goals", {}).get("for", {}).get("minute", {})
                            return {
                                "forme_str": form[-nb:] if form else "",
                                "victoires": form[-nb:].count("W") if form else 0,
                                "nuls": form[-nb:].count("D") if form else 0,
                                "defaites": form[-nb:].count("L") if form else 0
                            }
        except:
            pass
        return {}
        """Forme récente : derniers matchs avec buts marqués/encaissés"""
        try:
            resp = self.session.get(f"{BASE_URL}/fixtures", params={"team": team_name, "league": league_id, "season": "2026", "status": "FT"}, timeout=10)
            if resp.status_code == 200:
                matches = resp.json().get("response", [])[-nb:]
            if resp.status_code == 200:
                matches = resp.json().get("response", [])
                buts_marques = 0
                buts_encaisses = 0
                over25 = 0
                btts = 0
                for m in matches:
                    is_home = m["teams"]["home"]["name"] == team_name
                    scored = m["goals"]["home"] if is_home else m["goals"]["away"]
                    conceded = m["goals"]["away"] if is_home else m["goals"]["home"]
                    buts_marques += scored
                    buts_encaisses += conceded
                    if scored + conceded >= 3: over25 += 1
                    if scored > 0 and conceded > 0: btts += 1
                n = len(matches) or 1
                return {
                    "matchs": n,
                    "buts_marques": round(buts_marques/n, 1),
                    "buts_encaisses": round(buts_encaisses/n, 1),
                    "over25_pct": round(over25/n*100),
                    "btts_pct": round(btts/n*100)
                }
        except:
            pass
        return None

    def get_team_goals(self, team_name, league_id):
        try:
            resp = self.session.get(f"{BASE_URL}/teams", params={"search": team_name}, timeout=10)
            if resp.status_code == 200:
                for t in resp.json().get("response", []):
                    if t["team"]["name"] == team_name:
                        tid = t["team"]["id"]
                        r2 = self.session.get(f"{BASE_URL}/teams/statistics", params={"team": tid, "league": league_id, "season": "2026"}, timeout=10)
                        if r2.status_code == 200:
                            d = r2.json().get("response", {})
                            g = d.get("goals", {}).get("for", {})
                            return {
                                "domicile": g.get("total", {}).get("home", 0) or 0,
                                "exterieur": g.get("total", {}).get("away", 0) or 0,
                                "over15": g.get("under_over", {}).get("1.5", {}).get("over", 0) or 0,
                                "over25": g.get("under_over", {}).get("2.5", {}).get("over", 0) or 0,
                                "btts": 0
                            }
        except:
            pass
        return {}

    def get_team_cards(self, team_name, league_id):
        try:
            resp = self.session.get(f"{BASE_URL}/teams", params={"search": team_name}, timeout=10)
            if resp.status_code == 200:
                for t in resp.json().get("response", []):
                    if t["team"]["name"] == team_name:
                        tid = t["team"]["id"]
                        r2 = self.session.get(f"{BASE_URL}/teams/statistics", params={"team": tid, "league": league_id, "season": "2026"}, timeout=10)
                        if r2.status_code == 200:
                            d = r2.json().get("response", {})
                            c = d.get("cards", {})
                            return {"jaunes": c.get("yellow", {}).get("total", 0) or 0, "rouges": c.get("red", {}).get("total", 0) or 0}
        except:
            pass
        return {}

    def get_team_penalties(self, team_name, league_id):
        try:
            resp = self.session.get(f"{BASE_URL}/teams", params={"search": team_name}, timeout=10)
            if resp.status_code == 200:
                for t in resp.json().get("response", []):
                    if t["team"]["name"] == team_name:
                        tid = t["team"]["id"]
                        r2 = self.session.get(f"{BASE_URL}/teams/statistics", params={"team": tid, "league": league_id, "season": "2026"}, timeout=10)
                        if r2.status_code == 200:
                            p = r2.json().get("response", {}).get("penalty", {})
                            return {"marques": p.get("scored", {}).get("total", 0) or 0, "total": p.get("total", 0) or 0}
        except:
            pass
        return {}

    def get_team_failed_to_score(self, team_name, league_id):
        try:
            resp = self.session.get(f"{BASE_URL}/teams", params={"search": team_name}, timeout=10)
            if resp.status_code == 200:
                for t in resp.json().get("response", []):
                    if t["team"]["name"] == team_name:
                        tid = t["team"]["id"]
                        r2 = self.session.get(f"{BASE_URL}/teams/statistics", params={"team": tid, "league": league_id, "season": "2026"}, timeout=10)
                        if r2.status_code == 200:
                            fts = r2.json().get("response", {}).get("failed_to_score", {})
                            return {"total": fts.get("total", 0) or 0}
        except:
            pass
        return {}

    def get_player_full_stats(self, player_name, team_name):
        """Recherche par equipe + nom, plus fiable"""
        try:
            # Etape 1: chercher par equipe
            resp = self.session.get(f"{BASE_URL}/players", params={"team": team_name, "season": "2026"}, timeout=10)
            if resp.status_code == 200:
                for p in resp.json().get("response", []):
                    if player_name.lower() in p["player"]["name"].lower():
                        for s in p.get("statistics", []):
                            if s.get("team",{}).get("name") == team_name:
                                return self._parse_player_stats(s)
            # Etape 2: fallback recherche par nom
            resp = self.session.get(f"{BASE_URL}/players", params={"search": player_name, "season": "2026"}, timeout=10)
            if resp.status_code == 200:
                for p in resp.json().get("response", []):
                    for s in p.get("statistics", []):
                        if s.get("team",{}).get("name") == team_name:
                            return self._parse_player_stats(s)
        except:
            pass
        return None

    def _parse_player_stats(self, s):
        return {
            "matchs": s.get("games",{}).get("appearences",0) or 0,
            "minutes": s.get("games",{}).get("minutes",0) or 0,
            "buts": s.get("goals",{}).get("total",0) or 0,
            "passes_decisives": s.get("goals",{}).get("assists",0) or 0,
            "tirs": s.get("shots",{}).get("total",0) or 0,
            "tirs_cadres": s.get("shots",{}).get("on",0) or 0,
            "passes_cles": s.get("passes",{}).get("key",0) or 0,
            "dribbles_reussis": s.get("dribbles",{}).get("success",0) or 0,
            "duels_gagnes": s.get("duels",{}).get("won",0) or 0,
            "fautes_subies": s.get("fouls",{}).get("drawn",0) or 0,
            "cartons_jaunes": s.get("cards",{}).get("yellow",0) or 0,
            "cartons_rouges": s.get("cards",{}).get("red",0) or 0,
            "penalties_marques": s.get("penalty",{}).get("scored",0) or 0,
        }
        try:
            resp = self.session.get(f"{BASE_URL}/players", params={"search": player_name, "season": "2026"}, timeout=10)
            if resp.status_code == 200:
                for p in resp.json().get("response", []):
                    for s in p.get("statistics", []):
                        if s.get("team",{}).get("name") == team_name:
                            return {
                                "matchs": s.get("games",{}).get("appearences",0) or 0,
                                "minutes": s.get("games",{}).get("minutes",0) or 0,
                                "buts": s.get("goals",{}).get("total",0) or 0,
                                "passes_decisives": s.get("goals",{}).get("assists",0) or 0,
                                "tirs": s.get("shots",{}).get("total",0) or 0,
                                "tirs_cadres": s.get("shots",{}).get("on",0) or 0,
                                "passes_cles": s.get("passes",{}).get("key",0) or 0,
                                "dribbles_reussis": s.get("dribbles",{}).get("success",0) or 0,
                                "duels_gagnes": s.get("duels",{}).get("won",0) or 0,
                                "fautes_subies": s.get("fouls",{}).get("drawn",0) or 0,
                                "cartons_jaunes": s.get("cards",{}).get("yellow",0) or 0,
                                "cartons_rouges": s.get("cards",{}).get("red",0) or 0,
                                "penalties_marques": s.get("penalty",{}).get("scored",0) or 0,
                            }
        except:
            pass
        return None
