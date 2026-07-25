import logging
import requests
from config import FOOTBALL_DATA_API_KEY, COMPETITIONS

BASE_URL = "https://api.football-data.org/v4"

class FootballAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": FOOTBALL_DATA_API_KEY})

    def _request(self, endpoint, params=None):
        url = f"{BASE_URL}{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 403:
                return None
            if resp.status_code == 429:
                return None
            resp.raise_for_status()
            return resp.json()
        except:
            return None

    def get_fixtures(self, date):
        matches = []
        codes = list(COMPETITIONS.values())
        for code in codes:
            data = self._request(f"/competitions/{code}/matches", {"dateFrom": date, "dateTo": date})
            if data and "matches" in data:
                for m in data["matches"]:
                    if m["id"] not in [x["id"] for x in matches]:
                        matches.append(m)
        logging.info(f"football-data.org -> {len(matches)} match(es) on {date}")
        return matches

    def get_lineups(self, match_id):
        data = self._request(f"/matches/{match_id}")
        if data:
            home_lineup = data.get("homeTeam", {}).get("lineup", [])
            away_lineup = data.get("awayTeam", {}).get("lineup", [])
            if home_lineup or away_lineup:
                return {
                    "home": {"players": [{"player": {"name": p.get("name", "")}, "starting": True} for p in home_lineup]},
                    "away": {"players": [{"player": {"name": p.get("name", "")}, "starting": True} for p in away_lineup]},
                }
        return None

    def get_competition_name(self, match):
        comp = match.get("competition", {})
        return comp.get("name", "?")
