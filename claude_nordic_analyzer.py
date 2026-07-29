import os, json, re, requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-6"
NORDIC_LEAGUES = {"Allsvenskan", "Superliga", "Eliteserien"}

def _build_prompt(match):
    home = match["homeTeam"]["name"]
    away = match["awayTeam"]["name"]
    competition = match.get("competition", {}).get("name", "")
    date = match.get("utcDate", "")
    return f"""Tu es un analyste expert en paris sportifs. Ce championnat n'a pas de stats dans notre systeme - utilise la recherche web.

MATCH : {home} vs {away}
CHAMPIONNAT : {competition}
DATE : {date}

Cherche sur le web : compos probables, absences, forme 5 derniers matchs, split domicile/exterieur, H2H, joueurs en forme.
Sois honnete : si pas trouve, baisse la confiance. Termine par ce JSON UNIQUEMENT :
{{
  "over15": {{"probability": 0-100, "reason": "..."}},
  "over25": {{"probability": 0-100, "reason": "..."}},
  "btts": {{"probability": 0-100, "reason": "..."}},
  "victory": {{"pick": "home|draw|away", "probability": 0-100, "reason": "..."}},
  "conseil": "pari le plus solide et pourquoi"
}}"""

def analyze_nordic_match(match):
    prompt = _build_prompt(match)
    payload = {
        "model": MODEL, "max_tokens": 3000,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
    }
    headers = {"Content-Type": "application/json", "x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"}
    try:
        resp = requests.post(ANTHROPIC_URL, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"): return {"error": str(data["error"])}
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        full_text = "\n".join(text_blocks).strip()
        json_match = re.search(r"\{[\s\S]*\}", full_text)
        candidate = json_match.group(0) if json_match else full_text
        candidate = candidate.replace("```json", "").replace("```", "").strip()
        return json.loads(candidate)
    except Exception as e:
        return {"error": str(e)}
