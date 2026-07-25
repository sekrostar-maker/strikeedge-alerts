import logging
import requests
from datetime import datetime, timezone
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

API_BASE = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# football-data.org position → display label
POSITION_ORDER = ["Goalkeeper", "Defender", "Midfielder", "Offence"]
POSITION_LABEL  = {
    "Goalkeeper": "GK",
    "Defender":   "DEF",
    "Midfielder": "MID",
    "Offence":    "FWD",
}


class TelegramBot:
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        try:
            resp = requests.post(
                f"{API_BASE}/sendMessage",
                json={
                    "chat_id":                  TELEGRAM_CHAT_ID,
                    "text":                     text,
                    "parse_mode":               parse_mode,
                    "disable_web_page_preview": True,
                },
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            logging.error("Telegram send failed: %s", exc)
            return False

    def send_lineup_notification(self, fixture: dict, match_data: dict):
        """
        Format and send a lineup notification.
        `fixture`    — row dict from the DB (home_team, away_team, league_name, …)
        `match_data` — full match object from football-data.org /matches/{id}
        """
        home    = fixture["home_team"]
        away    = fixture["away_team"]
        league  = fixture["league_name"]
        minutes = fixture.get("minutes_to_kickoff", 0)

        try:
            kickoff_dt  = datetime.fromisoformat(fixture["kickoff_utc"].replace("Z", "+00:00"))
            kickoff_str = kickoff_dt.strftime("%H:%M UTC")
        except Exception:
            kickoff_str = "?"

        if minutes > 0:
            timing = f"in {minutes} min"
        elif minutes == 0:
            timing = "at kickoff"
        else:
            timing = f"kicked off {abs(minutes)} min ago"

        lines = [
            "⚽ <b>LINEUP ANNOUNCED</b>",
            "",
            f"🏆 {league}",
            f"🆚 <b>{home}</b>  vs  <b>{away}</b>",
            f"🕐 {kickoff_str}  ({timing})",
            "",
        ]

        teams = [
            ("🔵", match_data.get("homeTeam", {})),
            ("🔴", match_data.get("awayTeam", {})),
        ]

        for icon, team_data in teams:
            team_name = team_data.get("name", "Unknown")
            formation = team_data.get("formation") or "?"
            lineup    = team_data.get("lineup", [])
            bench     = team_data.get("bench", [])

            lines.append(f"{icon} <b>{team_name}</b>  [{formation}]")

            # Group starters by position in the standard order
            by_pos: dict[str, list[dict]] = {p: [] for p in POSITION_ORDER}
            for player in lineup:
                pos = player.get("position", "Midfielder")
                by_pos.setdefault(pos, []).append(player)

            for pos in POSITION_ORDER:
                players = by_pos.get(pos, [])
                if not players:
                    continue
                label       = POSITION_LABEL.get(pos, pos[:3].upper())
                player_strs = []
                for p in players:
                    num  = str(p.get("shirtNumber", "")).rjust(2)
                    name = p.get("name", "")
                    player_strs.append(f"<code>{num}</code> {name}")
                lines.append(f"   <b>{label}</b>  " + "  ·  ".join(player_strs))

            if bench:
                bench_names = [p.get("name", "") for p in bench[:9]]
                lines.append(f"   <i>Bench: {', '.join(bench_names)}</i>")

            lines.append("")

        message = "\n".join(lines).strip()
        ok = self.send_message(message)
        if ok:
            logging.info("✅ Lineup alert sent: %s vs %s (%s)", home, away, league)
        else:
            logging.warning("❌ Failed to send lineup alert: %s vs %s", home, away)
