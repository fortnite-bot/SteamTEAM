import json

def beschrijvende_statistieken(data_path):
    """
    Analyseer de dataset en geef beschrijvende statistieken terug.
    """
    try:
        # Laad de data
        with open(data_path, 'r') as f:
            data = json.load(f)

        # Extract data
        prices = [game.get("price", 0) for game in data if isinstance(game.get("price", 0), (int, float))]
        playtimes = [game.get("average_playtime", 0) for game in data if isinstance(game.get("average_playtime", 0), (int, float))]

        # Bereken statistieken
        beschrijvende_resultaten = {
            "Gemiddelde Prijs": sum(prices) / len(prices) if prices else 0,
            "Mediaan Prijs": sorted(prices)[len(prices)//2] if prices else 0,
            "Gemiddelde Speeltijd": sum(playtimes) / len(playtimes) if playtimes else 0,
            "Mediaan Speeltijd": sorted(playtimes)[len(playtimes)//2] if playtimes else 0,
        }

        # Bouw een overzichtelijke string
        result = "\n".join([f"{key}: {value:.2f}" for key, value in beschrijvende_resultaten.items()])
        return result

    except Exception as e:
        return f"Fout bij het uitvoeren van beschrijvende statistieken: {e}"
