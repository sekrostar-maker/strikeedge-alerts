
from database_enrichie import get_db

class MismatchAnalyzer:
    def __init__(self):
        self.db = get_db()
    
    def analyser_match(self, match_info, lineups):
        alertes = []
        alertes.extend(self._analyser_cote(lineups.get('domicile', []), lineups.get('exterieur', [])))
        alertes.extend(self._analyser_cote(lineups.get('exterieur', []), lineups.get('domicile', [])))
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:5]
    
    def _analyser_cote(self, attaquants_noms, defenseurs_noms):
        alertes = []
        attaquants = self._get_joueurs(attaquants_noms)
        defenseurs = self._get_joueurs(defenseurs_noms)
        if not defenseurs:
            return alertes
        for attaquant in attaquants:
            score = 0
            facteurs = []
            for defenseur in defenseurs:
                if attaquant.get('est_rapide') and defenseur.get('est_lent'):
                    score += 30
                    facteurs.append({'type': 'VITESSE', 'detail': f"{attaquant['nom']} rapide vs {defenseur['nom']} LENT"})
                if attaquant.get('est_bon_dribble') and defenseur.get('est_mauvais_1v1'):
                    score += 25
                    facteurs.append({'type': 'TECHNIQUE', 'detail': f"{attaquant['nom']} dribbleur vs {defenseur['nom']} faible 1v1"})
                if attaquant.get('est_bon_tete') and defenseur.get('est_faible_aerien'):
                    score += 25
                    facteurs.append({'type': 'AERIEN', 'detail': f"{attaquant['nom']} bon tete vs {defenseur['nom']} faible air"})
            if attaquant.get('buts_90min', 0) > 0.3:
                score += min(20, attaquant['buts_90min'] * 30)
                facteurs.append({'type': 'STATS', 'detail': f"{attaquant['buts_90min']:.1f} buts/90min"})
            probabilite = min(90, score)
            if probabilite >= 50:
                alertes.append({'attaquant': attaquant['nom'], 'probabilite': probabilite, 'facteurs': facteurs})
        return alertes
    
    def _get_joueurs(self, noms):
        joueurs = []
        c = self.db.cursor()
        for nom in noms:
            c.execute("SELECT * FROM player_profiles WHERE nom LIKE ?", (f'%{nom.split()[-1]}%',))
            row = c.fetchone()
            if row:
                joueurs.append(dict(row))
            else:
                joueurs.append({'nom': nom, 'est_rapide': 0, 'est_lent': 0, 'est_bon_tete': 0, 'est_faible_aerien': 0, 'est_bon_dribble': 0, 'est_mauvais_1v1': 0, 'buts_90min': 0})
        return joueurs
