from brain import Brain
from football_api import FootballAPI

class AnalysisEngine:
    def __init__(self):
        self.brain = Brain()
        self.api = FootballAPI()
    
    def analyse_match_sans_lineups(self, match):
        """Analyse sans compos : stats equipes, tendances, H2H"""
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        lid = match.get('league_id', '119')
        
        home_stats = self.api.get_team_stats(home, lid) or {}
        away_stats = self.api.get_team_stats(away, lid) or {}
        h2h = self.api.get_h2h_teams(home, away)
        
        alertes = []
        
        # Buts domicile vs defense exterieur
        hm = home_stats.get('matchs', 0) or 1
        am = away_stats.get('matchs', 0) or 1
        home_buts = home_stats.get('buts_marques', 0) / hm if hm > 0 else 0
        away_encaisses = away_stats.get('buts_encaisses', 0) / am if am > 0 else 0
        
        if home_buts > 0 and away_encaisses > 0:
            if home_buts > 1.5 and away_encaisses > 1.2:
                score = min(80, (home_buts + away_encaisses) * 20)
                alertes.append({
                    'type': 'equipe',
                    'equipe': home,
                    'probabilite': score,
                    'pourquoi': f"{home} marque {round(home_buts,1)} buts/match, {away} encaisse {round(away_encaisses,1)} buts/match. Forte probabilite de buts pour {home}."
                })

        # Buts exterieur vs defense domicile
        away_buts = away_stats.get('buts_marques', 0) / am if am > 0 else 0
        home_encaisses = home_stats.get('buts_encaisses', 0) / hm if hm > 0 else 0
        
        if away_buts > 0 and home_encaisses > 0:
            if away_buts > 1.5 and home_encaisses > 1.2:
                score = min(80, (away_buts + home_encaisses) * 20)
                alertes.append({
                    'type': 'equipe',
                    'equipe': away,
                    'probabilite': score,
                    'pourquoi': f"{away} marque {round(away_buts,1)} buts/match, {home} encaisse {round(home_encaisses,1)} buts/match."
                })
        
        # H2H : confrontations directes
        if h2h and h2h['total'] >= 3:
            total_buts = h2h['buts_team1'] + h2h['buts_team2']
            moy = total_buts / h2h['total']
            if moy > 2.5:
                alertes.append({
                    'type': 'h2h',
                    'equipe': '',
                    'probabilite': min(75, moy * 25),
                    'pourquoi': f"Moyenne de {round(moy,1)} buts lors des {h2h['total']} dernieres confrontations entre {home} et {away}."
                })
        
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:3]
