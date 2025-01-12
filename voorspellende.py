import json

# Open het Steam json bestand
with open('./steam.json', 'r') as file:
    data = json.load(file)


# Onafhankelijke variabele (X) = prijs
prices = [d['price'] for d in data]

# Afhankelijke variabele (y) = gemiddelde speeltijd
average_playtimes = [d['average_playtime'] for d in data]

# Parameters en instellingen
m = 0                       # Startwaarde van de helling van de regressielijn
b = 0                       # Startwaarde van het intercept
learning_rate = 0.00001     # Kleine learning rate omdat de data groot is
iterations = 2000           # Aantal herhalingen voor de gradient descent

# Gradient descent
for _ in range(iterations):
    m_gradient = 0
    b_gradient = 0
    n = len(prices)

    # Bereken gradients voor m en b
    for i in range(n):
        y_pred = m * prices[i] + b                                      # Voorspelde waarde berekenen
        m_gradient += -2 * prices[i] * (average_playtimes[i] - y_pred)  # Afgeleide m
        b_gradient += -2 * (average_playtimes[i] - y_pred)              # Afgeleide b

    # Update m en b
    m -= (m_gradient / n) * learning_rate   # Geeft aan hoe de gemiddelde speeltijd verandert als de prijs van een spel verandert
    b -= (b_gradient / n) * learning_rate   # Het punt waar de regressielijn de verticale as (de y-as) kruist.

# Output wat m en b inhoud
print(f"De gemiddelde speeltijd neemt toe met {m:.2f} minuten voor elke "
      f"euro die de prijs van een spel stijgt")
print(f"De gemiddelde speeltijd is {b:.2f} minuten"
      f" wanneer de prijs van een spel 0 euro is\n")

# Voorspel de gemiddelde speeltijden op basis van prijzen
predictions = [m * x + b for x in prices] # Lineaire regressielijn formule
print(f"Gemiddelde voorspelde speeltijd: {sum(predictions) / len(predictions):.2f} minuten")
print(f"Minimale voorspelde speeltijd: {min(predictions):.2f} minuten")
print(f"Maximale voorspelde speeltijd: {max(predictions):.2f} minuten")

# De grafiek met de orginele data
import matplotlib.pyplot as plt

# Filter de originele data
filtered_prices = [p for p, t in zip(prices, average_playtimes) if t < 50000]
filtered_playtimes = [t for t in average_playtimes if t < 50000]

# Plot de originele data
plt.figure(figsize=(10, 6))
plt.scatter(filtered_prices, filtered_playtimes, color='blue', alpha=0.5, s=13, label='Data')

# Plot de regressielijn
x_range = [min(filtered_prices), max(filtered_prices)]
y_range = [m * x + b for x in x_range]
plt.plot(x_range, y_range, color='red', label='Regressielijn')


plt.title("Relatie tussen prijs en gemiddelde speeltijd van games", fontsize=14)
plt.xlabel("Prijs (€)", fontsize=12)
plt.ylabel("Gemiddelde speeltijd (minuten)", fontsize=12)
plt.xlim(0, 80)  # Prijzen tot €100 voor meer duidelijkheid
plt.ylim(0, 5000)  # Speeltijd tot 5000 minuten voor meer duidelijkheid
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(fontsize=10)
plt.show()
