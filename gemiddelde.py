import requests

# De API-link en parameters
url = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/"
params = {
    "key": "281C1716E751A37C4A73A7AAF53ADA1D",  # Jouw API-sleutel
    "steamid": "76561198081621942"              # Steam ID
}

# Data ophalen
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    if "response" in data and "games" in data["response"]:
        games = data["response"]["games"]

        # Haal speeltijden op
        playtimes = [game["playtime_forever"] for game in games]

        # Controleer of er speeltijden zijn
        if len(playtimes) > 0:
            # Bereken de gemiddelde speeltijd in minuten
            average_playtime_minutes = sum(playtimes) / len(playtimes)

            # Converteer naar uren en resterende minuten
            hours = int(average_playtime_minutes // 60)  # Aantal uren
            minutes = int(average_playtime_minutes % 60)  # Restant minuten

            print(f"Gemiddelde speeltijd: {hours} uur en {minutes} minuten")
        else:
            print("Geen speeltijden beschikbaar.")
    else:
        print("Geen games gevonden in de API-response.")
else:
    print(f"API-fout: {response.status_code}")

