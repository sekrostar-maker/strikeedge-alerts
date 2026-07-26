from brain import Brain
from football_api import FootballAPI

class AnalysisEngine:
    def __init__(self):
        self.brain = Brain()
        self.api = FootballAPI()
    
    def analyse_match_sans_lineups(self, match):
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        lid = match.get('league_id', '119')
        
        hs = self.api.get_team_stats(home, lid) or {}
        as_ = self.api.get_team_stats(away, lid) or {}
        xg_h = self.api.get_team_xg(home, lid) or {}
        xg_a = self.api.get_team_xg(away, lid) or {}
        h2h = self.api.get_h2h_teams(home, away)
        
        hm = hs.get('matchs', 1) or 1
        am = as_.get('matchs', 1) or 1
        
        alertes = []
        
        # === OVER 2.5 ===
        h_marque = hs.get('buts_marques', 0) / hm if hm > 0 else 0
        h_encaisse = hs.get('buts_encaisses', 0) / hm if hm > 0 else 0
        a_marque = as_.get('buts_marques', 0) / am if am > 0 else 0
        a_encaisse = as_.get('buts_encaisses', 0) / am if am > 0 else 0
        
        moy_buts = h_marque + a_marque + h_encaisse + a_encaisse
        over25_prob = min(90, moy_buts * 25)
        
        if over25_prob >= 50:
            alertes.append({
                'type': 'OVER 2.5 buts',
                'probabilite': over25_prob,
                'pourquoi': f"{home}: {round(h_marque,1)} marques/{round(h_encaisse,1)} encaisses. {away}: {round(a_marque,1)} marques/{round(a_encaisse,1)} encaisses par match."
            })

        # === OVER 1.5 ===
        over15_prob = min(92, moy_buts * 30)
        if over15_prob >= 55:
            alertes.append({
                'type': 'OVER 1.5 buts',
                'probabilite': over15_prob,
                'pourquoi': f"{home}: {round(h_marque,1)} marques/{round(h_encaisse,1)} encaisses. {away}: {round(a_marque,1)} marques/{round(a_encaisse,1)} encaisses."
            })
        
        # === BTTS ===
        btts_score = ((h_marque + a_encaisse) / 2 + (a_marque + h_encaisse) / 2) * 20
        btts_prob = min(88, btts_score)
        if btts_prob >= 45:
            alertes.append({
                'type': 'BTTS OUI',
                'probabilite': btts_prob,
                'pourquoi': f"{home} marque {round(h_marque,1)} et encaisse {round(h_encaisse,1)}. {away} marque {round(a_marque,1)} et encaisse {round(a_encaisse,1)}."
            })
        
        # === VICTOIRE ===
        diff_home = h_marque - a_encaisse
        diff_away = a_marque - h_encaisse
        
        if diff_home > 0.5:
            prob = min(85, 50 + diff_home * 15)
            alertes.append({
                'type': f'VICTOIRE {home}',
                'probabilite': prob,
                'pourquoi': f"{home} marque {round(h_marque,1)} buts/match, {away} encaisse {round(a_encaisse,1)}."
            })
        
        if diff_away > 0.5:
            prob = min(85, 50 + diff_away * 15)
            alertes.append({
                'type': f'VICTOIRE {away}',
                'probabilite': prob,
                'pourquoi': f"{away} marque {round(a_marque,1)} buts/match, {home} encaisse {round(h_encaisse,1)}."
            })
        
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:4]

        # === OVER 1.5 ===
        over15_prob = min(92, moy_buts * 30)
        if over15_prob >= 55:
            alertes.append({
                'type': 'OVER 1.5 buts',
                'probabilite': over15_prob,
                'pourquoi': f"{home}: {round(h_marque,1)} marques/{round(h_encaisse,1)} encaisses. {away}: {round(a_marque,1)} marques/{round(a_encaisse,1)} encaisses."
            })

        # === BTTS ===
        btts_score = ((h_marque + a_encaisse) / 2 + (a_marque + h_encaisse) / 2) * 20
        btts_prob = min(88, btts_score)
        if btts_prob >= 45:
            alertes.append({
                'type': 'BTTS OUI',
                'probabilite': btts_prob,
                'pourquoi': f"{home} marque {round(h_marque,1)} et encaisse {round(h_encaisse,1)}. {away} marque {round(a_marque,1)} et encaisse {round(a_encaisse,1)}."
            })

        # === VICTOIRE ===
        diff_home = h_marque - a_encaisse
        diff_away = a_marque - h_encaisse
        if diff_home > 0.5:
            prob = min(85, 50 + diff_home * 15)
            alertes.append({
                'type': f'VICTOIRE {home}',
                'probabilite': prob,
                'pourquoi': f"{home} marque {round(h_marque,1)} buts/match, {away} encaisse {round(a_encaisse,1)}."
            })
        if diff_away > 0.5:
            prob = min(85, 50 + diff_away * 15)
            alertes.append({
                'type': f'VICTOIRE {away}',
                'probabilite': prob,
                'pourquoi': f"{away} marque {round(a_marque,1)} buts/match, {home} encaisse {round(h_encaisse,1)}."
            })
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:4]
