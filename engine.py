from brain import Brain
from football_api import FootballAPI
import json

class AnalysisEngine:
    def __init__(self):
        self.brain = Brain()
        self.api = FootballAPI()
    
    def build_stats_block(self, match):
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        lid = match.get('league_id', '')
        hs = self.api.get_team_stats(home, lid) or {}
        as_ = self.api.get_team_stats(away, lid) or {}
        h2h = self.api.get_h2h_teams(home, away)
        form_h = self.api.get_team_form(home, lid) or {}
        form_a = self.api.get_team_form(away, lid) or {}
        hm = hs.get('matchs', 0) or 1
        am = as_.get('matchs', 0) or 1
        
        block = f"""MATCH: {home} vs {away}

🏠 {home}
  Matchs: {hs.get('matchs',0)}
  Buts marques: {hs.get('buts_marques',0)}
  Buts encaisses: {hs.get('buts_encaisses',0)}
  Clean sheets: {hs.get('clean_sheets',0)}
  xG pour: {round(hs.get('xg_pour',0),1)}
  xG contre: {round(hs.get('xg_contre',0),1)}
  Forme: {form_h.get('forme_str','?')}

🏟️ {away}
  Matchs: {as_.get('matchs',0)}
  Buts marques: {as_.get('buts_marques',0)}
  Buts encaisses: {as_.get('buts_encaisses',0)}
  Clean sheets: {as_.get('clean_sheets',0)}
  xG pour: {round(as_.get('xg_pour',0),1)}
  xG contre: {round(as_.get('xg_contre',0),1)}
  Forme: {form_a.get('forme_str','?')}
"""
        if h2h and h2h['total'] > 0:
            block += f"""
📊 H2H: {h2h['total']} matchs
  Buts {home}: {h2h['buts_team1']}
  Buts {away}: {h2h['buts_team2']}
  Moyenne: {round((h2h['buts_team1']+h2h['buts_team2'])/h2h['total'],1)}/match
"""
        block += """
Analyse et donne probabilites (%) + resume pour OVER 1.5, OVER 2.5, BTTS OUI, VICTOIRE.
Reponds en JSON uniquement."""
        return block
  Forme: {form_a.get("forme_str","?")}
        if h2h and h2h['total'] > 0:
            block += f"""
📊 H2H: {h2h['total']} matchs
  Buts {home}: {h2h['buts_team1']} | {away}: {h2h['buts_team2']}
  Moyenne: {round((h2h['buts_team1']+h2h['buts_team2'])/h2h['total'],1)}/match
"""
        block += """
Analyse et donne probabilites (%) + resume pour OVER 1.5, OVER 2.5, BTTS OUI, VICTOIRE.
Reponds en JSON uniquement."""
        return block

    def analyse_with_deepseek(self, match):
        """Envoie les stats a DeepSeek et recupere les probas"""
        block = self.build_stats_block(match)
        # DeepSeek API (gratuite)
        try:
            import requests
            r = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": "Bearer DEEPSEEK_API_KEY", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": block}], "temperature": 0.3},
                timeout=30
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except:
            pass
        return None

    def analyse_match_sans_lineups(self, match):
        # Tenter DeepSeek d'abord
        result = self.analyse_with_deepseek(match)
        if result:
            try:
                data = json.loads(result)
                alertes = []
                for k, v in data.items():
                    if isinstance(v, dict) and v.get('prob', 0) >= 60:
                        alertes.append({
                            'type': k.replace('_', ' '),
                            'probabilite': v['prob'],
                            'pourquoi': v.get('resume', '')
                        })
                alertes.sort(key=lambda x: x['probabilite'], reverse=True)
                return alertes[:4]
            except:
                pass
        
        # Fallback: calcul basique
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        lid = match.get('league_id', '')
        hs = self.api.get_team_stats(home, lid) or {}
        as_ = self.api.get_team_stats(away, lid) or {}
        hm = hs.get('matchs', 1) or 1
        am = as_.get('matchs', 1) or 1
        h_marque = hs.get('buts_marques', 0) / hm
        h_encaisse = hs.get('buts_encaisses', 0) / hm
        a_marque = as_.get('buts_marques', 0) / am
        a_encaisse = as_.get('buts_encaisses', 0) / am
        alertes = []
        over15 = 55 + (h_marque + a_marque + h_encaisse + a_encaisse) * 8
        if over15 >= 60:
            alertes.append({'type': 'OVER 1.5 buts', 'probabilite': min(92, over15), 'pourquoi': f"{home}: {round(h_marque,1)}M/{round(h_encaisse,1)}E - {away}: {round(a_marque,1)}M/{round(a_encaisse,1)}E"})
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:2]
