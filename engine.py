"""Moteur d'analyse - Probabilités et résumés parlants"""
from brain import Brain
from football_api import FootballAPI

class AnalysisEngine:
    def __init__(self):
        self.brain = Brain()
        self.api = FootballAPI()
    
    def analyse_match(self, match):
        """Analyse un match et retourne les recommandations buteurs"""
        mid = match['id']
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        championnat = match.get('competition', {}).get('name', '?')
        
        lineups = self.api.get_lineups(mid)
        if not lineups:
            return []
        
        alertes = []
        
        for side, att_team, def_team in [('home', home, away), ('away', away, home)]:
            for p in lineups[side]['players'][:11]:
                nom = p['player']['name']
                # Chercher les stats du joueur
                stats = self.api.get_player_stats(nom, att_team)
                if not stats:
                    continue
                
                buts = stats.get('buts', 0)
                matchs = stats.get('matchs', 1) or 1
                
                # Score de base : buts par match
                score = (buts / matchs) * 100 if matchs > 0 else 0
                raisons = []

                # Bonus: forme récente
                forme = self.brain.get_player_form(nom)
                if forme and forme['matchs'] >= 3 and forme['buts'] >= 2:
                    score += 15
                    raisons.append(f"{forme['buts']} buts lors des {forme['matchs']} derniers matchs")
                
                # Bonus: H2H contre cette équipe
                h2h = self.brain.get_h2h(nom, def_team)
                if h2h and h2h['matchs_joues'] >= 2 and h2h['buts_marques'] >= 2:
                    score += 20
                    raisons.append(f"A marque {h2h['buts_marques']} buts lors de ses {h2h['matchs_joues']} derniers matchs contre {def_team}")
                
                # Bonus: tirs cadrés
                tirs_cadres = stats.get('tirs_cadres', 0)
                if matchs > 0 and tirs_cadres / matchs > 1:
                    score += 10
                    raisons.append(f"{round(tirs_cadres/matchs,1)} tirs cadrés par match en moyenne")
                
                # Bonus: dribbles
                dribbles = stats.get('dribbles', 0)
                if matchs > 0 and dribbles / matchs > 1.5:
                    score += 5
                    raisons.append("Joueur percutant par ses dribbles")

                # Générer le résumé parlant
                pourquoi = ""
                if raisons:
                    pourquoi = f"{nom} ({att_team}) a de bonnes chances contre {def_team}. "
                    pourquoi += " ".join(raisons) + "."
                
                # Ajouter l'alerte si probabilité > 40%
                score = min(90, score)
                if score >= 40 and pourquoi:
                    alertes.append({
                        'attaquant': f"{nom} ({att_team})",
                        'probabilite': score,
                        'pourquoi': pourquoi
                    })
        
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:5]
