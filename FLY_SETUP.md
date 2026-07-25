# Deploying to Fly.io (free, always-on)

This bot runs as a background worker on Fly.io's free tier.
Follow these steps once — after that, it runs forever automatically.

---

## Step 1 — Install the Fly CLI

Open a terminal on your computer and run:

```bash
curl -L https://fly.io/install.sh | sh
```

On Windows, use PowerShell:
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

---

## Step 2 — Sign up / log in

```bash
fly auth signup    # new account
# or
fly auth login     # existing account
```

A browser window opens — sign in with Google or GitHub (no credit card required for the free tier).

---

## Step 3 — Go to the football-alerts folder

In the Replit shell (or your terminal if you cloned the repo):

```bash
cd football-alerts
```

---

## Step 4 — Create the app

```bash
fly launch --no-deploy
```

When prompted:
- **App name**: accept the default or choose your own (e.g. `my-football-alerts`)
- **Region**: pick the one closest to you (e.g. `ams` for Europe, `lhr` for UK)
- **PostgreSQL / Redis**: say **No** to both
- **Deploy now**: say **No** (we set secrets first)

> If it asks to overwrite `fly.toml`, say **No** — the existing one is already configured correctly.

---

## Step 5 — Create the persistent volume (saves your SQLite database)

```bash
fly volumes create football_data --size 1 --region ams
```

Replace `ams` with the same region you chose above.

---

## Step 6 — Set your secrets

```bash
fly secrets set \
  TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN" \
  TELEGRAM_CHAT_ID="YOUR_CHAT_ID" \
  FOOTBALL_DATA_API_KEY="YOUR_API_KEY"
```

Replace the values with your actual tokens (same ones saved in Replit Secrets).

---

## Step 7 — Deploy

```bash
fly deploy
```

This builds the Docker image and starts the bot. Takes about 1–2 minutes.

---

## Step 8 — Verify it's running

```bash
fly logs
```

You should see:
```
⚽ Football Lineup Alert Bot is running (football-data.org)
Monitoring 10 competitions: Premier League, Ligue 1, ...
```

---

## Useful commands

| Command | What it does |
|---|---|
| `fly logs` | View live logs |
| `fly status` | Check if the app is running |
| `fly restart` | Restart the bot |
| `fly secrets set KEY=value` | Update a secret |
| `fly deploy` | Push a code update |
| `fly scale show` | Show current VM size (should be shared-cpu-1x) |

---

## Cost

The free tier includes **3 shared VMs** and **3 GB of volume storage**.
This bot uses 1 VM + ~1 MB of storage. You have 2 free VMs left for other projects.

No credit card is required unless you go over the free allowance.
