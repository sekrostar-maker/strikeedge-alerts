#!/usr/bin/env python3
"""
Helper script to find your Telegram Chat ID.

Steps:
  1. Open Telegram and send ANY message to your bot
  2. Run:  python get_chat_id.py
  3. Copy the Chat ID shown and save it as the TELEGRAM_CHAT_ID secret
"""

import os
import sys
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

if not TOKEN:
    print("❌  TELEGRAM_BOT_TOKEN is not set.")
    print("    Add it as a Replit Secret first, then re-run this script.")
    sys.exit(1)

resp = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=10)
data = resp.json()

if not data.get("ok"):
    print(f"❌  Telegram API error: {data.get('description', data)}")
    sys.exit(1)

updates = data.get("result", [])
if not updates:
    print("⚠️  No messages found.")
    print("    Please send any message to your bot, then run this script again.")
    sys.exit(0)

seen: set[int] = set()
print("\n✅  Chats found:\n")
for update in updates:
    msg  = update.get("message") or update.get("channel_post") or {}
    chat = msg.get("chat", {})
    cid  = chat.get("id")
    if cid is None or cid in seen:
        continue
    seen.add(cid)
    ctype = chat.get("type", "")
    name  = (
        chat.get("title")
        or chat.get("username")
        or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
    )
    print(f"  Chat ID : {cid}")
    print(f"  Name    : {name}")
    print(f"  Type    : {ctype}")
    print(f"  → Save  {cid}  as TELEGRAM_CHAT_ID in Replit Secrets")
    print()
