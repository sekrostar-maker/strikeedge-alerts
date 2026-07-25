import os
import json
import kagglehub

USERNAME = os.environ.get("KAGGLE_USERNAME", "")
TOKEN = os.environ.get("KAGGLE_TOKEN", "")
os.environ["KAGGLE_USERNAME"] = USERNAME
os.environ["KAGGLE_KEY"] = TOKEN

print("Telechargement du dataset Kaggle...")
path = kagglehub.dataset_download("hubertsidorowicz/football-players-stats-2025-2026")
print(f"Dataset telecharge dans: {path}")

import pandas as pd
import glob

files = glob.glob(f"{path}/**/*.csv", recursive=True)
for f in files:
    print(f"Fichier trouve: {f}")
    df = pd.read_csv(f)
    print(f"Colonnes: {list(df.columns)[:10]}")
    print(f"Lignes: {len(df)}")
    print(df.head(2))
