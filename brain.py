import sqlite3, json, os
DB_PATH = os.path.join(os.path.dirname(__file__), "strikeedge_brain.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_brain():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS matchs (
        id INTEGER PRIMARY KEY, match_id_api INTEGER UNIQUE,
        date TEXT, championnat TEXT, domicile TEXT, exterieur TEXT,
        score_domicile INTEGER, score_exterieur INTEGER,
        lineup_home TEXT, lineup_away TEXT, stats_json TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS player_match_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id_api INTEGER, joueur TEXT, equipe TEXT,
        buts INTEGER, xg REAL, tirs INTEGER, tirs_cadres INTEGER,
        dribbles INTEGER, duels_aeriens INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS h2h (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        joueur TEXT, equipe_adverse TEXT,
        matchs_joues INTEGER DEFAULT 0, buts_marques INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS defensive_impact (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        defenseur TEXT, equipe TEXT,
        matchs_avec INTEGER DEFAULT 0, buts_encaisses_avec REAL DEFAULT 0,
        matchs_sans INTEGER DEFAULT 0, buts_encaisses_sans REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS alert_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT, match_id_api INTEGER, joueur_predit TEXT,
        probabilite REAL, a_marque INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

class Brain:
    def __init__(self):
        init_brain()
        self.db = get_db()
    
    def save_match(self, m):
        c = self.db.cursor()
        c.execute('''INSERT OR REPLACE INTO matchs 
            (match_id_api, date, championnat, domicile, exterieur, lineup_home, lineup_away)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (m['id'], m['date'], m['championnat'],
             m['domicile'], m['exterieur'],
             json.dumps(m.get('lineup_home', [])),
             json.dumps(m.get('lineup_away', []))))
        self.db.commit()

    def add_player_stat(self, match_id, joueur, equipe, stats):
        c = self.db.cursor()
        c.execute('''INSERT INTO player_match_stats 
            (match_id_api, joueur, equipe, buts, xg, tirs, tirs_cadres, dribbles, duels_aeriens)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (match_id, joueur, equipe,
             stats.get('buts', 0), stats.get('xg', 0),
             stats.get('tirs', 0), stats.get('tirs_cadres', 0),
             stats.get('dribbles', 0), stats.get('duels_aeriens', 0)))
        self.db.commit()
        # Update H2H si le joueur a marqué
        if stats.get('buts', 0) > 0:
            self._update_h2h(joueur, equipe)

    def _update_h2h(self, joueur, equipe_adverse):
        c = self.db.cursor()
        c.execute('SELECT * FROM h2h WHERE joueur=? AND equipe_adverse=?', (joueur, equipe_adverse))
        row = c.fetchone()
        if row:
            c.execute('UPDATE h2h SET matchs_joues=matchs_joues+1, buts_marques=buts_marques+1 WHERE joueur=? AND equipe_adverse=?', (joueur, equipe_adverse))
        else:
            c.execute('INSERT INTO h2h (joueur, equipe_adverse, matchs_joues, buts_marques) VALUES (?, ?, 1, 1)', (joueur, equipe_adverse))
        self.db.commit()

    def get_h2h(self, joueur, equipe_adverse):
        c = self.db.cursor()
        c.execute('SELECT * FROM h2h WHERE joueur=? AND equipe_adverse=?', (joueur, equipe_adverse))
        row = c.fetchone()
        return dict(row) if row else None

    def get_player_form(self, joueur, nb=5):
        c = self.db.cursor()
        c.execute('SELECT * FROM player_match_stats WHERE joueur=? ORDER BY id DESC LIMIT ?', (joueur, nb))
        rows = c.fetchall()
        if rows:
            buts = sum(r['buts'] or 0 for r in rows)
            return {'matchs': len(rows), 'buts': buts, 'moyenne': round(buts/len(rows), 2)}
        return None

    def save_alert_result(self, date, match_id, joueur, probabilite, a_marque):
        c = self.db.cursor()
        c.execute('INSERT INTO alert_history (date, match_id_api, joueur_predit, probabilite, a_marque) VALUES (?, ?, ?, ?, ?)',
                  (date, match_id, joueur, probabilite, a_marque))
        self.db.commit()

    def get_success_rate(self):
        c = self.db.cursor()
        c.execute('SELECT COUNT(*) as total, SUM(a_marque) as reussis FROM alert_history')
        row = c.fetchone()
        if row and row['total'] > 0:
            return round(row['reussis'] / row['total'] * 100, 1)
        return None

    def get_brain_stats(self):
        c = self.db.cursor()
        c.execute('SELECT COUNT(*) FROM matchs')
        matchs = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM player_match_stats')
        stats = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM h2h')
        h2h = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM alert_history')
        alertes = c.fetchone()[0]
        return f"🧠 Cerveau: {matchs} matchs, {stats} stats joueurs, {h2h} H2H, {alertes} alertes"

    def save_prediction(self, match_id, match_name, prediction_type, prob, result=None):
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, match_id_api INTEGER, match_name TEXT,
            prediction_type TEXT, probability REAL, result TEXT)''')
        c.execute('INSERT INTO predictions (date, match_id_api, match_name, prediction_type, probability, result) VALUES (?, ?, ?, ?, ?, ?)',
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), match_id, match_name, prediction_type, prob, result))
        self.db.commit()

    def update_prediction_result(self, match_name, prediction_type, result):
        c = self.db.cursor()
        c.execute('UPDATE predictions SET result=? WHERE match_name=? AND prediction_type=? AND result IS NULL',
                  (result, match_name, prediction_type))
        self.db.commit()

    def get_success_rate(self):
        c = self.db.cursor()
        c.execute('''SELECT prediction_type, COUNT(*) as total, 
                     SUM(CASE WHEN result="GAGNE" THEN 1 ELSE 0 END) as gagne
                     FROM predictions WHERE result IS NOT NULL 
                     GROUP BY prediction_type ORDER BY total DESC''')
        rows = c.fetchall()
        stats = {}
        for r in rows:
            total = r['total']
            gagne = r['gagne'] or 0
            stats[r['prediction_type']] = {"total": total, "gagne": gagne, "taux": round(gagne/total*100) if total > 0 else 0}
        return stats

    def save_prediction(self, match_id, match_name, pred_type, prob, result=None):
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT, match_id_api INTEGER, match_name TEXT,
            prediction_type TEXT, probability REAL, result TEXT)''')
        c.execute('INSERT INTO predictions (date, match_id_api, match_name, prediction_type, probability, result) VALUES (?, ?, ?, ?, ?, ?)',
                  (datetime.now().strftime("%Y-%m-%d %H:%M"), match_id, match_name, pred_type, prob, result))
        self.db.commit()

    def update_result(self, match_name, pred_type, result):
        c = self.db.cursor()
        c.execute('UPDATE predictions SET result=? WHERE match_name=? AND prediction_type=? AND result IS NULL', (result, match_name, pred_type))
        self.db.commit()

    def get_success_rate(self):
        c = self.db.cursor()
        c.execute('''SELECT prediction_type, COUNT(*) as total, 
                     SUM(CASE WHEN result="GAGNE" THEN 1 ELSE 0 END) as gagne
                     FROM predictions WHERE result IS NOT NULL 
                     GROUP BY prediction_type ORDER BY total DESC''')
        rows = c.fetchall()
        stats = {}
        for r in rows:
            t = r['total']
            g = r['gagne'] or 0
            stats[r['prediction_type']] = {"total": t, "gagne": g, "taux": round(g/t*100) if t>0 else 0}
        return stats
