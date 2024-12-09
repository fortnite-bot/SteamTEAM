import json

with open('C:\\Users\\Sharo\\Downloads\\steam.json', 'r') as f:
    data = json.load(f)

# Functie om het gemiddelde te berekenen
def calculate_mean(data):
    total = 0
    for value in data:
        total += value  # Tel alle waarden bij elkaar op
    return total / len(data)  # Deel door het aantal waarden

# Functie om de mediaan te berekenen
def calculate_median(data):
    sorted_data = sorted(data)  # Sorteer de data
    n = len(sorted_data)
    mid = n // 2  # Vind het midden van de lijst

    if n % 2 == 0:  # Als het aantal waarden even is
        return (sorted_data[mid - 1] + sorted_data[mid]) / 2
    else:  # Als het aantal waarden oneven is
        return sorted_data[mid]

# Extract data
prices = [game["price"] for game in data]
average_playtimes = [game["average_playtime"] for game in data]

# Bereken gemiddelde en mediaan
mean_price = calculate_mean(prices)
median_price = calculate_median(prices)

mean_playtime = calculate_mean(average_playtimes)
median_playtime = calculate_median(average_playtimes)

# Resultaten tonen
print(f"Gemiddelde prijs: {mean_price:.2f} euro")
print(f"Mediaan prijs: {median_price:.2f} euro")
print(f"Gemiddelde speeltijd: {mean_playtime:.2f} minuten")
print(f"Mediaan speeltijd: {median_playtime:.2f} minuten")

