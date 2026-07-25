import logging
import requests
from config import FOOTBALL_DATA_API_KEY, COMPETITIONS

BASE_URL = "https://api.football-data.org/v4"


class FootballAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": FOOTBALL_DATA_API_KEY})

    def _request(self, endpoint: str, params: dict | None = None) -> dict | None:
        url = f"{BASE_URL}{endpoint}"
        try:
            resp = self.session.get(url, params=params, timeout=15)
            if resp.status_code == 403:
                logging.warning("Access denied for %s — competition may require a paid plan", url)
                return None
            if resp.status_code == 429:
                logging.warning("Rate limited by football-data.org — will retry next cycle")
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logging.error("Timeout calling %s", url)
        except requests.exceptions.RequestException as exc:
            logging.error("Request error for %s: %s", url, exc)
        except Exception as exc:
            logging.error("Unexpected error for %s: %s", url, exc)
        return None

    def get_competition_name(self, match: dict) -> str:
        """Resolve our friendly league name from the match's competition code."""
        code = match.get("competition", {}).get("code", "")
        for name, c in COMPETITIONS.items():
            if c == code:
                return name
        return match.get("competition", {}).get("name", code)

    def get_fixtures(self, date: str) -> list[dict]:
        """
        Fetch ALL fixtures across every configured competition for a given date
        in a single API request.
        """
        codes = ",".join(COMPETITIONS.values())
        data  = self._request("/matches", {"dateFrom": date, "dateTo": date, "competitions": codes})
        if not data:
            return []
        matches = data.get("matches", [])
        logging.info("football-data.org → %d match(es) found on %s", len(matches), date)
        return matches

    def get_lineups(self, match_id: int) -> dict | None:
        """
        Fetch the full match object.  Returns the match dict if both starting
        lineups are confirmed, otherwise None.
        """
        data = self._request(f"/matches/{match_id}")
        if not data:
            return None
        home_lineup = data.get("homeTeam", {}).get("lineup", [])
        away_lineup = data.get("awayTeam", {}).get("lineup", [])
        if home_lineup and away_lineup:
            return data
        return None
