import json

with open('C:\\Users\\Sharo\\Downloads\\steam.json', 'r') as file:
    data = json.load(file)


# Onafhankelijke variabele (X) = prijs
prices = [d['price'] for d in data]

# Afhankelijke variabele (y) = gemiddelde speeltijd
average_playtimes = [d['average_playtime'] for d in data]

# Parameters initialiseren
m = 0  # Helling (slope)
b = 0  # Intercept
learning_rate = 0.000001  # Kleine learning rate omdat de data groot is
iterations = 1000  # Aantal herhalingen

# Gradient descent
for _ in range(iterations):
    m_gradient = 0
    b_gradient = 0
    n = len(prices)

    # Bereken gradients voor m en b
    for i in range(n):
        y_pred = m * prices[i] + b  # Voorspelde waarde
        m_gradient += -2 * prices[i] * (average_playtimes[i] - y_pred)  # Afgeleide m
        b_gradient += -2 * (average_playtimes[i] - y_pred)  # Afgeleide b

    # Update m en b
    m -= (m_gradient / n) * learning_rate
    b -= (b_gradient / n) * learning_rate

# Toon de uiteindelijke waarden van m en b
print(f"Geoptimaliseerde m (helling): {m}")
print(f"Geoptimaliseerde b (intercept): {b}")

# Maak voorspellingen op basis van prijzen
predictions = [m * x + b for x in prices]

print("Voorspellingen:", predictions)

import matplotlib.pyplot as plt

# Plot de originele data
plt.scatter(prices, average_playtimes, color='blue', label='Gegevens')

# Plot de regressielijn
x_range = [min(prices), max(prices)]
y_range = [m * x + b for x in x_range]
plt.plot(x_range, y_range, color='red', label='Regressielijn')

plt.xlabel("Prijs (€)")
plt.ylabel("Gemiddelde speeltijd (minuten)")
plt.legend()
plt.show()
