from brain import Brain
from football_api import FootballAPI

class AnalysisEngine:
    def __init__(self):
        self.brain = Brain()
        self.api = FootballAPI()
    
    def analyse_match(self, match):
        mid = match['id']
        home = match['homeTeam']['name']
        away = match['awayTeam']['name']
        championnat = match.get('competition', {}).get('name', '?')
        league_id = match.get('league_id', '119')
        
        lineups = self.api.get_lineups(mid)
        if not lineups:
            return []
        
        def_home = self.api.get_team_stats(home, league_id) or {}
        def_away = self.api.get_team_stats(away, league_id) or {}
        abs_home = self.api.get_absences(home)
        abs_away = self.api.get_absences(away)
        xg_home = self.api.get_team_xg(home, league_id) or {}
        xg_away = self.api.get_team_xg(away, league_id) or {}
        
        alertes = []
        for side, att_team, def_team, def_stats, absences, xg_def in [
            ('home', home, away, def_away, abs_away, xg_away),
            ('away', away, home, def_home, abs_home, xg_home)
        ]:
            for p in lineups[side]['players'][:11]:
                nom = p['player']['name']
                stats = self.api.get_player_detailed_stats(nom, att_team) or {}
                adv = self.api.get_player_advanced_stats(nom, att_team) or {}
                
                buts = stats.get('buts_total', 0)
                matchs = stats.get('matchs', 1) or 1
                score = (buts / matchs) * 100 if matchs > 0 else 0
                raisons = []

                # Forme récente
                forme = self.brain.get_player_form(nom)
                if forme and forme['matchs'] >= 3 and forme['buts'] >= 2:
                    score += 15
                    raisons.append(f"{forme['buts']} buts lors des {forme['matchs']} derniers matchs")
                
                # H2H joueur
                h2h = self.brain.get_h2h(nom, def_team)
                if h2h and h2h['matchs_joues'] >= 2 and h2h['buts_marques'] >= 2:
                    score += 20
                    raisons.append(f"a marque {h2h['buts_marques']} buts contre {def_team}")
                
                # Buts de la tête
                buts_tete = stats.get('buts_tete', 0)
                if buts > 0 and buts_tete / buts > 0.3:
                    score += 10
                    raisons.append(f"{round(buts_tete/buts*100)}% de ses buts de la tete")
                
                # Fautes subies
                fautes = stats.get('fautes_subies', 0)
                if matchs > 0 and fautes / matchs > 2:
                    score += 8
                    raisons.append(f"provoque {round(fautes/matchs,1)} fautes par match")
                
                # xG joueur
                xg_j = stats.get('xg', 0)
                if matchs > 0 and xg_j / matchs > 0.3:
                    score += 10
                    raisons.append(f"xG de {round(xg_j/matchs,2)} par match")
                
                # Duels aériens %
                da_g = adv.get('duels_aeriens_gagnes', 0)
                da_t = adv.get('duels_aeriens_total', 1) or 1
                if da_t > 0 and da_g / da_t > 0.5:
                    score += 8
                    raisons.append(f"domine dans les airs ({round(da_g/da_t*100)}% duels gagnes)")
                
                # Passes décisives
                pd = adv.get('passes_decisives', 0)
                if pd >= 3:
                    score += 8
                    raisons.append(f"{pd} passes decisives cette saison")
                
                # Penaltys
                pm = adv.get('penalties_marques', 0)
                if pm >= 2:
                    score += 6
                    raisons.append(f"tireur de penalty ({pm} marques)")

                # Penaltys
                pm = adv.get("penalties_marques", 0)
                if pm >= 2:
                    score += 6
                    raisons.append(f"tireur de penalty ({pm} marques)")
                # Passes decisives
                pd = adv.get('passes_decisives', 0)
                if pd >= 3:
                    score += 8
                    raisons.append(f"{pd} passes decisives cette saison")
                # Defense febrile
                be = def_stats.get('buts_encaisses', 0)
                md = def_stats.get('matchs', 1) or 1
                if md > 0 and be / md > 1.5:
                    score += 10
                    raisons.append(f"{def_team} encaisse {round(be/md,1)} buts par match")
                # xG contre
                xg_c = xg_def.get('xg_contre', 0)
                if md > 0 and xg_c / md > 1.3:
                    score += 8
                    raisons.append(f"{def_team} xG contre eleve ({round(xg_c/md,1)}/match)")
                # Absences
                if absences:
                    score += 10
                    raisons.append(f"{def_team} prive de {', '.join(absences[:2])}")
                
                pourquoi = ""
                if raisons:
                    pourquoi = f"{nom} ({att_team}) a de bonnes chances contre {def_team}. " + " ".join(raisons) + "."
                score = min(90, score)
                if score >= 35 and pourquoi:
                    alertes.append({'attaquant': f"{nom} ({att_team})", 'probabilite': score, 'pourquoi': pourquoi})
        
        alertes.sort(key=lambda x: x['probabilite'], reverse=True)
        return alertes[:5]
