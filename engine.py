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
        form_h = self.api.get_team_form(home, lid) or {}
        form_a = self.api.get_team_form(away, lid) or {}
        
        hm = hs.get('matchs', 1) or 1
        am = as_.get('matchs', 1) or 1
        
        h_marque = hs.get('buts_marques', 0) / hm
        h_encaisse = hs.get('buts_encaisses', 0) / hm
        a_marque = as_.get('buts_marques', 0) / am
        a_encaisse = as_.get('buts_encaisses', 0) / am
        
        h_xg = xg_h.get('xg_pour', 0) / hm if hm > 0 else 0
        h_xga = xg_h.get('xg_contre', 0) / hm if hm > 0 else 0
        a_xg = xg_a.get('xg_pour', 0) / am if am > 0 else 0
        a_xga = xg_a.get('xg_contre', 0) / am if am > 0 else 0
        
        alertes = []
        SEUIL = 60

        # OVER 2.5
        over25 = 30
        if h_marque > 1.2: over25 += 10
        if a_marque > 1.2: over25 += 10
        if h_encaisse > 1.2: over25 += 10
        if a_encaisse > 1.2: over25 += 10
        if h_xg + h_xga > 2.5: over25 += 8
        if a_xg + a_xga > 2.5: over25 += 8
        if form_h.get('over25_pct', 0) > 50: over25 += 8
        if form_a.get('over25_pct', 0) > 50: over25 += 8
        if h2h and h2h['total'] > 0:
            moy = (h2h['buts_team1'] + h2h['buts_team2']) / h2h['total']
            if moy > 2.5: over25 += 10
        over25 = min(88, over25)
        if over25 >= SEUIL:
            alertes.append({'type': 'OVER 2.5 buts', 'probabilite': over25, 'pourquoi': f"{home} ({round(h_marque,1)}M/{round(h_encaisse,1)}E) - {away} ({round(a_marque,1)}M/{round(a_encaisse,1)}E)"})

        # OVER 1.5
        over15 = 55
        if h_marque > 0.8: over15 += 8
        if a_marque > 0.8: over15 += 8
        if h_encaisse > 0.8: over15 += 8
        if a_encaisse > 0.8: over15 += 8
        if h_xg + a_xg > 1.8: over15 += 6
        if form_h.get('matchs', 0) >= 3: over15 += 5
        if form_a.get('matchs', 0) >= 3: over15 += 5
        over15 = min(94, over15)
        if over15 >= SEUIL:
            alertes.append({'type': 'OVER 1.5 buts', 'probabilite': over15, 'pourquoi': f"{home} ({round(h_marque,1)}M/{round(h_encaisse,1)}E) - {away} ({round(a_marque,1)}M/{round(a_encaisse,1)}E)"})

        # BTTS
        btts = 25
        if h_marque > 1 and a_encaisse > 1: btts += 12
        if a_marque > 1 and h_encaisse > 1: btts += 12
        if h_marque > 0.8 and a_marque > 0.8: btts += 8
        if h_xga > 1.2: btts += 6
        if a_xga > 1.2: btts += 6
        if form_h.get('btts_pct', 0) > 50: btts += 8
        if form_a.get('btts_pct', 0) > 50: btts += 8
        btts = min(86, btts)
        if btts >= SEUIL:
            alertes.append({'type': 'BTTS OUI', 'probabilite': btts, 'pourquoi': f"{home} ({round(h_marque,1)}M/{round(h_encaisse,1)}E) - {away} ({round(a_marque,1)}M/{round(a_encaisse,1)}E)"})

        # VICTOIRE
        diff_home = h_marque - a_encaisse
        diff_away = a_marque - h_encaisse
        if diff_home > 0.4:
            prob = 35 + diff_home * 16 + (form_h.get('buts_marques', 0) - form_a.get('buts_encaisses', 0)) * 5
            prob = min(82, prob)
            if prob >= SEUIL:
                alertes.append({'type': f'VICTOIRE {home}', 'probabilite': prob, 'pourquoi': f"{home} ({round(h_marque,1)}M) vs {away} ({round(a_encaisse,1)}E)"})
        if diff_away > 0.4:
            prob = 35 + diff_away * 16 + (form_a.get('buts_marques', 0) - form_h.get('buts_encaisses', 0)) * 5
            prob = min(82, prob)
            if prob >= SEUIL:
                alertes.append({'type': f'VICTOIRE {away}', 'probabilite': prob, 'pourquoi': f"{away} ({round(a_marque,1)}M) vs {home} ({round(h_encaisse,1)}E)"})
        
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:4]
