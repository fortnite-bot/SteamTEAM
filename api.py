import requests

# De API-link
url = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/"
params = {
    "key": "281C1716E751A37C4A73A7AAF53ADA1D",  # Jouw API-sleutel
    "steamid": "76561198081621942"              # Steam ID
}

# Verzoek naar de API sturen
response = requests.get(url, params=params)

# Controleren of het verzoek succesvol was
if response.status_code == 200:
    # JSON-gegevens omzetten naar een Python-dict
    data = response.json()

    # Check of de 'response' data bevat
    if "response" in data and "games" in data["response"]:
        games = data["response"]["games"]
        for game in games:
            name = game["name"]
            playtime_minutes = game["playtime_forever"]
            playtime_hours = playtime_minutes / 60  # Minuten omzetten naar uren
            print(f"Game: {name}, Speeltijd: {playtime_hours:.2f} uur")
    else:
        print("Geen games gevonden in de API-response.")
else:
    print(f"API-fout: {response.status_code}")



