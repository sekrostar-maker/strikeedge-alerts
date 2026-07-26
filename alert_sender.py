import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def envoyer_alertes(match_info, alertes):
    if not alertes:
        return
    m = "⚽ " + match_info.get("domicile","?") + " vs " + match_info.get("exterieur","?") + "\n"
    m += "🕐 " + match_info.get("heure","?") + " | " + match_info.get("championnat","?") + "\n\n"
    for a in alertes[:3]:
        if a.get('attaquant'):
            m += "◉ " + a["attaquant"] + " → " + str(int(a["probabilite"])) + "%\n"
        else:
            m += "📊 " + a.get('type','Analyse') + " → " + str(int(a["probabilite"])) + "%\n"
        if a.get("pourquoi"):
            m += "   💡 " + a["pourquoi"] + "\n"
        m += "\n"
    requests.post("https://api.telegram.org/bot"+TELEGRAM_BOT_TOKEN+"/sendMessage", json={"chat_id":TELEGRAM_CHAT_ID,"text":m})
