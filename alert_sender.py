import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def envoyer_alertes(match_info, alertes):
    if not alertes:
        return
    m = "⚽ " + match_info.get("domicile","?") + " vs " + match_info.get("exterieur","?") + "\n"
    m += "🕐 " + match_info.get("heure","?")[:16] + " | " + match_info.get("championnat","?") + "\n\n"
    for a in alertes[:4]:
        m += "▪️ " + a.get('type','') + " → " + str(int(a["probabilite"])) + "%\n"
        m += "   " + a.get("pourquoi","") + "\n\n"
    requests.post("https://api.telegram.org/bot"+TELEGRAM_BOT_TOKEN+"/sendMessage", json={"chat_id":TELEGRAM_CHAT_ID,"text":m})
