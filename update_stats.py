import requests
import csv
import json
import io

URLS = {
    "Bresil": "https://fbref.com/fr/comps/24/stats/Statistiques-Serie-A-Bresilienne.csv",
}

def download_and_parse(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/csv,text/html,*/*",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Referer": "https://fbref.com/",
    }
    r = requests.get(url, headers=headers, timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        return []
    
    content = r.text
    reader = csv.reader(io.StringIO(content))
    players = []
    
    for row in reader:
        if len(row) < 11:
            continue
        try:
            nom = row[1].strip()
            club = row[4].strip()
            buts = float(row[10]) if row[10] else 0
            tirs = float(row[8]) if row[8] else 0
            tirs_cadres = float(row[9]) if row[9] else 0
            xg = float(row[16]) if len(row) > 16 and row[16] else 0
            matchs = int(row[6]) if row[6].isdigit() else 0
            
            if nom and nom != "Player" and nom != "Joueur" and buts > 0:
                players.append({
                    "nom": nom,
                    "club": club,
                    "buts": buts,
                    "buts_90": round(buts / (matchs * 0.7), 2) if matchs > 0 else 0,
                    "tirs_90": round(tirs / (matchs * 0.7), 2) if matchs > 0 else 0,
                    "tirs_cadres_90": round(tirs_cadres / (matchs * 0.7), 2) if matchs > 0 else 0,
                    "xg_90": round(xg / (matchs * 0.7), 2) if matchs > 0 else 0,
                    "matchs": matchs
                })
        except:
            continue
    
    players.sort(key=lambda x: x["buts"], reverse=True)
    return players

if __name__ == "__main__":
    all_players = {}
    for league, url in URLS.items():
        print(f"Telechargement {league}...")
        players = download_and_parse(url)
        all_players[league] = players
        print(f"  {len(players)} joueurs trouves")
    
    with open("players_stats.json", "w") as f:
        json.dump(all_players, f, indent=2)
    
    total = sum(len(p) for p in all_players.values())
    print(f"\nTotal: {total} joueurs sauvegardes dans players_stats.json")
