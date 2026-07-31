from brain import Brain
from football_api import FootballAPI
from claude_nordic_analyzer import analyze_nordic_match
import json, logging
log = logging.getLogger(__name__)

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
        pen_h = self.api.get_team_penalties(home, lid) or {}
        pen_a = self.api.get_team_penalties(away, lid) or {}
        fts_h = self.api.get_team_failed_to_score(home, lid) or {}
        fts_a = self.api.get_team_failed_to_score(away, lid) or {}
        form_a = self.api.get_team_form(away, lid) or {}
        cards_h = self.api.get_team_cards(home, lid) or {}
        cards_a = self.api.get_team_cards(away, lid) or {}
        goals_h = self.api.get_team_goals(home, lid) or {}
        goals_a = self.api.get_team_goals(away, lid) or {}
        
        block = f"""MATCH: {home} vs {away}

🏠 {home}
  Matchs: {hs.get('matchs',0)}
  Buts marques: {hs.get('buts_marques',0)} (dom: {goals_h.get('domicile',0)}, ext: {goals_h.get('exterieur',0)})
  Buts encaisses: {hs.get('buts_encaisses',0)}
  Clean sheets: {hs.get('clean_sheets',0)}
  Over 1.5: {goals_h.get('over15',0)}/{hs.get('matchs',0)} matchs
  Over 2.5: {goals_h.get('over25',0)}/{hs.get('matchs',0)} matchs
  BTTS: {goals_h.get('btts',0)}/{hs.get('matchs',0)} matchs
  Cartons jaunes: {cards_h.get('jaunes',0)}, rouges: {cards_h.get('rouges',0)}
  Forme: {form_h.get('forme_str','?')}

🏟️ {away}
  Matchs: {as_.get('matchs',0)}
  Buts marques: {as_.get('buts_marques',0)} (dom: {goals_a.get('domicile',0)}, ext: {goals_a.get('exterieur',0)})
  Buts encaisses: {as_.get('buts_encaisses',0)}
  Clean sheets: {as_.get('clean_sheets',0)}
  Over 1.5: {goals_a.get('over15',0)}/{as_.get('matchs',0)} matchs
  Over 2.5: {goals_a.get('over25',0)}/{as_.get('matchs',0)} matchs
  BTTS: {goals_a.get('btts',0)}/{as_.get('matchs',0)} matchs
  Cartons jaunes: {cards_a.get('jaunes',0)}, rouges: {cards_a.get('rouges',0)}
  Forme: {form_a.get('forme_str','?')}
"""
        if h2h and h2h['total'] > 0:
            block += f"""
📊 H2H: {h2h['total']} matchs
  {home}: {h2h['buts_team1']} buts | {away}: {h2h['buts_team2']} buts
  Moyenne: {round((h2h['buts_team1']+h2h['buts_team2'])/h2h['total'],1)}/match
"""
        block += """
Analyse et donne probabilites (%) + resume pour:
- OVER 1.5 buts
- OVER 2.5 buts
- BTTS OUI
- VICTOIRE (quelle equipe)
Reponds en JSON uniquement avec un champ "conseil" qui indique le pari le plus recommande."""
        return block

    def analyse_with_groq(self, match):
        """Envoie les stats a Groq (Llama 3) et recupere les probas"""
        block = self.build_stats_block(match)
        try:
            import requests
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": "Bearer ${secrets.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": block}], "temperature": 0.3},
                timeout=30
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
        except:
            pass
        return None

    def analyse_match_sans_lineups(self, match):
        competition = match.get('competition', {}).get('name', '')
        if competition in ['Allsvenskan', 'Superliga', 'Eliteserien']:
            claude_result = analyze_nordic_match(match)
                log.info('Claude result: %s', str(claude_result)[:100])
            if claude_result and 'error' not in claude_result:
                return self._parse_claude_result(claude_result)
            result = None
        else:
            result = self.analyse_with_groq(match)
        if result:
            try:
                data = json.loads(result)
                alertes = []
                for k, v in data.items():
                    if isinstance(v, dict) and v.get('prob') or v.get('probabilite', 0) >= 60:
                        alertes.append({'type': k.replace('_',' '), 'probabilite': v['prob'], 'pourquoi': v.get('resume','')})
                alertes.sort(key=lambda x: x['probabilite'], reverse=True)
                return alertes[:4]
            except:
                pass
        # Fallback basique
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        lid = match.get('league_id','')
        hs = self.api.get_team_stats(home, lid) or {}
        as_ = self.api.get_team_stats(away, lid) or {}
        hm = hs.get('matchs',1) or 1
        am = as_.get('matchs',1) or 1
        h_marque = hs.get('buts_marques',0)/hm
        a_marque = as_.get('buts_marques',0)/am
        alertes = []
        over15 = 55 + (h_marque + a_marque)*10
        if over15 >= 60:
            alertes.append({'type':'OVER 1.5 buts','probabilite':min(90,over15),'pourquoi':f'{home}: {round(h_marque,1)}M - {away}: {round(a_marque,1)}M'})
        return alertes[:2]

    def _parse_claude_result(self, data):
        alertes = []
        for key, label in [('over15','OVER 1.5'),('over25','OVER 2.5'),('btts','BTTS'),('victory','VICTOIRE')]:
            if key in data and isinstance(data[key], dict):
                prob = data[key].get('probability', 0)
                if key == 'victory':
                    prob = data[key].get('probability', 0)
                if prob >= 60:
                    alertes.append({'type': label, 'probabilite': prob, 'pourquoi': data[key].get('reason','')})
        if data.get('conseil'):
            alertes.append({'type': 'CONSEIL', 'probabilite': 100, 'pourquoi': data['conseil']})
        if data.get('scorer') and data['scorer'].get('player'):
            s = data['scorer']
            alertes.append({'type': f'BUTEUR {s.get("player","?")} ({s.get("team","?")})', 'probabilite': s.get('confidence', 0), 'pourquoi': s.get('reason', '')})
        return alertes[:4]
