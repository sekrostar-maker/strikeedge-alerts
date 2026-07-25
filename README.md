# ⚽ Football Lineup Alert Bot

Sends Telegram notifications when starting lineups are announced for matches in your configured leagues.

## How it works

1. **On startup** — fetches today's fixtures from football-data.org for all 10 competitions in **one API call** and stores them in SQLite3.
2. **Every 20 minutes** — checks lineups for any fixture starting within the next 2 hours.
3. **When lineups drop** — sends a formatted Telegram message with both starting elevens (grouped by position) and bench players.
4. **Daily at 06:00 & 12:00 UTC** — refreshes the fixture list to pick up any late additions.

## Required secrets (set in Replit Secrets panel)

| Secret | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Chat/channel ID to receive alerts |
| `FOOTBALL_DATA_API_KEY` | Free API key from https://www.football-data.org/client/register |

## Finding your Telegram Chat ID

1. Open Telegram and send any message to your bot
2. Run: `python football-alerts/get_chat_id.py`
3. Copy the Chat ID and save it as `TELEGRAM_CHAT_ID` in Secrets

## Competitions monitored (football-data.org free tier)

| League | Code |
|---|---|
| Premier League | PL |
| Ligue 1 | FL1 |
| Serie A | SA |
| Bundesliga | BL1 |
| Brazil Serie A | BSA |
| Eredivisie | DED |
| Primeira Liga | PPL |
| Championship | ELC |
| Copa Libertadores | CLI |
| MLS | MLS |

> **Note:** Scandinavian/Icelandic leagues (Eliteserien, Allsvenskan, Veikkausliiga, Urvalsdeild) and Argentina's Primera División are not available on football-data.org's free plan.

## API efficiency

- **2 requests/day** for all fixture data (one call covers all 10 leagues simultaneously)
- **~1 request per fixture** for lineup checks (only checked in the 2-hour pre-kickoff window)
- Stays far under football-data.org's free tier limit of 10 requests/minute
