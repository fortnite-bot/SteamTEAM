import json

def beschrijvende_statistieken(data_path):
    """
    Analyseer de dataset en geef beschrijvende statistieken terug.
    """
    try:
        # Laad de data
        data = data_path

        # Filter gegevens (prijs en gemiddelde speeltijd)
        prices = []
        for d in data:
            d = list(d)
            price = d[2]
            if isinstance(price, (int, float)):
                prices.append(price)

        playtimes = []
        for d in data:
            d = list(d)
            average_playtime = d[3]
            if isinstance(average_playtime, (int, float)):
                playtimes.append(average_playtime)
        

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
