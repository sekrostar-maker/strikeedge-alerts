import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
def envoyer_alertes(match_info, alertes):
 if not alertes: return
 m = "⚽ " + match_info.get("domicile","?") + " vs " + match_info.get("exterieur","?") + "\n"
 m += "🕐 " + match_info.get("heure","?") + "\n\n"
 for a in alertes[:3]:
  m += "◉ " + a["attaquant"] + " → " + str(int(a["probabilite"])) + "%\n"
  raisons = []
  for f in a.get("facteurs",[]):
   raisons.append(f["type"])
  if raisons: m += "   " + " + ".join(raisons) + "\n"
  m += "\n"
 requests.post("https://api.telegram.org/bot"+TELEGRAM_BOT_TOKEN+"/sendMessage",json={"chat_id":TELEGRAM_CHAT_ID,"text":m})
