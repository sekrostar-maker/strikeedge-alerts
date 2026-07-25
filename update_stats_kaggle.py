import requests
from bs4 import BeautifulSoup
import json

URL = "https://fbref.com/fr/comps/24/stats/Statistiques-Serie-A-Bresilienne"

def scrape_fbref():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHubActions/1.0)",
        "Accept": "text/html,*/*",
        "Accept-Language": "fr-FR",
    }
    r = requests.get(URL, headers=headers, timeout=30)
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", id="stats_standard")
        if table:
            rows = table.find_all("tr")
            players = []
            for row in rows:
                cells = row.find_all(["th", "td"])
                if len(cells) > 15:
                    try:
                        nom = cells[0].text.strip()
                        club = cells[3].text.strip()
                        buts = cells[10].text.strip()
                        tirs = cells[8].text.strip()
                        tirs_cadres = cells[9].text.strip()
                        xg = cells[16].text.strip() if len(cells) > 16 else "0"
                        matchs = cells[5].text.strip()
                        
                        if nom and nom != "Joueur" and buts.replace(".","").isdigit():
                            players.append({
                                "nom": nom, "club": club,
                                "buts": float(buts) if buts else 0,
                                "tirs_90": float(tirs) if tirs else 0,
                                "tirs_cadres_90": float(tirs_cadres) if tirs_cadres else 0,
                                "xg_90": float(xg) if xg else 0,
                                "matchs": int(matchs) if matchs.isdigit() else 0
                            })
                    except:
                        continue
            
            players.sort(key=lambda x: x["buts"], reverse=True)
            with open("players_stats.json", "w", encoding="utf-8") as f:
                json.dump(players, f, indent=2, ensure_ascii=False)
            print(f"✅ {len(players)} joueurs sauvegardes")
            return
    print("❌ Échec")

if __name__ == "__main__":
    scrape_fbref()
