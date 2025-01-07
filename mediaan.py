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
            # Sorteer de lijst
            playtimes.sort()

            # Bereken de mediaan
            n = len(playtimes)
            if n % 2 == 1:  # Oneven aantal
                median_playtime = playtimes[n // 2]
            else:  # Even aantal
                median_playtime = (playtimes[n // 2 - 1] + playtimes[n // 2]) / 2

            # Omzetten van minuten naar uren
            median_playtime_hours = median_playtime / 60

            # Print alleen de mediaan in uren
            print(f"Mediaan speeltijd: {median_playtime_hours:.2f} uur")
        else:
            print("Geen speeltijden beschikbaar.")
    else:
        print("Geen games gevonden in de API-response.")
else:
    print(f"API-fout: {response.status_code}")

