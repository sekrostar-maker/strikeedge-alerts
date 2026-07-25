import os

TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID", "")
FOOTBALL_DATA_API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")

DB_PATH = os.environ.get(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "football_alerts.db"),
)

# Competition codes for football-data.org free tier
# https://www.football-data.org/coverage
# Note: Scandinavian/Icelandic leagues (Eliteserien, Allsvenskan, Veikkausliiga,
# Urvalsdeild) and Argentina's Primera División are not available on the free tier.
COMPETITIONS: dict[str, str] = {
    "Premier League":    "PL",
    "Ligue 1":           "FL1",
    "Serie A":           "SA",
    "Bundesliga":        "BL1",
    "Brazil Serie A":    "BSA",
    "Eredivisie":        "DED",
    "Primeira Liga":     "PPL",
    "Championship":      "ELC",
    "Copa Libertadores": "CLI",
    "MLS":               "MLS",
}

# How many minutes before kickoff to start checking for lineups
LINEUP_CHECK_START_MINUTES = 120
# Stop checking after kickoff has passed by this many minutes
LINEUP_CHECK_STOP_MINUTES  = 15
