import sqlite3,os
DB_NAME=os.path.join(os.path.dirname(__file__),"players.db")
def get_db():
 conn=sqlite3.connect(DB_NAME);conn.row_factory=sqlite3.Row;return conn
def init_db():
 c=get_db().cursor()
 c.execute("CREATE TABLE IF NOT EXISTS player_profiles(id INTEGER PRIMARY KEY AUTOINCREMENT,nom TEXT,club TEXT,position TEXT,vitesse_kmh REAL,est_lent INTEGER DEFAULT 0,est_faible_aerien INTEGER DEFAULT 0,est_mauvais_1v1 INTEGER DEFAULT 0,est_rapide INTEGER DEFAULT 0,est_bon_tete INTEGER DEFAULT 0,est_bon_dribble INTEGER DEFAULT 0,buts_90min REAL)")
 c.connection.commit()
