def beschrijvende_statistieken(data):
    
    import json

    # Functie om het gemiddelde te berekenen
    def gemiddelde(data):
        return sum(data) / len(data)

    # Functie om de mediaan te berekenen
    def mediaan(data):
        sorted_data = sorted(data)  # Sorteer de data
        n = len(sorted_data)
        mid = n // 2                # Vind het midden van de lijst

        if n % 2 == 0: # Als het aantal waarden even is
            return (sorted_data[mid - 1] + sorted_data[mid]) / 2
        else: # Als het aantal waarden oneven is
            return sorted_data[mid]

    # We nemen de waardes 'price' en 'average_playtime'
    prices = [game["price"] for game in data]
    average_playtimes = [game["average_playtime"] for game in data]

    # Bereken gemiddelde en mediaan van de bovenste waardes
    gemiddelde_prijs = gemiddelde(prices)
    mediaan_prijs = mediaan(prices)

    gemiddelde_speeltijd = gemiddelde(average_playtimes)
    mediaan_speeltijd = mediaan(average_playtimes)

    # De output van het gemiddelde en mediaan
    print(f"Gemiddelde prijs van alle games: {gemiddelde_prijs:.2f} euro")
    print(f"Mediaan prijs van alle games: {mediaan_prijs:.2f} euro")
    print(f"Gemiddelde speeltijd van alle games: {gemiddelde_speeltijd:.2f} minuten")
    print(f"Mediaan speeltijd van alle games: {mediaan_speeltijd:.2f} minuten")

