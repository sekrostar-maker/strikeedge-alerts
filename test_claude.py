import os, requests, json

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
print("KEY exists:", bool(KEY))
print("KEY start:", KEY[:15] if KEY else "VIDE")

if KEY:
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": "claude-sonnet-4-6", "max_tokens": 50, "messages": [{"role": "user", "content": "Dis OK"}]},
        timeout=30
    )
    print("Status:", r.status_code)
    if r.status_code == 200:
        print("REPONSE:", r.json()["content"][0]["text"][:100])
    else:
        print("ERREUR:", r.text[:200])
