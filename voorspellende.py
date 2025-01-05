import json
import numpy as np
import matplotlib.pyplot as plt

def voorspellende_analyse(data_path):
    """
    Voer een lineaire regressie uit om de relatie tussen prijs en gemiddelde speeltijd te analyseren.
    :param data_path: Pad naar de JSON-bestand met Steam-data
    :return: String met resultaten van de analyse
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

        average_playtimes = []
        for d in data:
            d = list(d)
            average_playtime = d[3]
            if isinstance(average_playtime, (int, float)):
                average_playtimes.append(average_playtime)

        if not prices or not average_playtimes:
            return "Geen geldige gegevens gevonden voor prijs en gemiddelde speeltijd."

        # Zet gegevens om in numpy-arrays voor eenvoudiger verwerking
        X = np.array(prices)
        y = np.array(average_playtimes)

        # Initialiseer parameters
        m = 0  # Helling (slope)
        b = 0  # Intercept
        learning_rate = 0.000001
        iterations = 1000

        # Gradient descent
        n = len(X)
        for _ in range(iterations):
            y_pred = m * X + b
            m_gradient = (-2 / n) * np.sum(X * (y - y_pred))
            b_gradient = (-2 / n) * np.sum(y - y_pred)
            m -= learning_rate * m_gradient
            b -= learning_rate * b_gradient

        # Voorspellingen op basis van geoptimaliseerde m en b
        predictions = m * X + b

        # Plot de resultaten
        plt.figure(figsize=(10, 6))
        plt.scatter(X, y, color='blue', label='Gegevens')
        plt.plot(X, predictions, color='red', label='Regressielijn')
        plt.xlabel("Prijs (€)")
        plt.ylabel("Gemiddelde speeltijd (minuten)")
        plt.title("Lineaire Regressie: Prijs vs Gemiddelde Speeltijd")
        plt.legend()
        plt.grid(True)
        plt.savefig("./voorspellende_analyse_plot.png")  # Sla de plot op als bestand
        plt.close()

        # Bouw een resultaatstring
        result = (
            f"Lineaire regressie voltooid:\n"
            f"- Geoptimaliseerde helling (m): {m:.4f}\n"
            f"- Geoptimaliseerde intercept (b): {b:.4f}\n\n"
            f"De regressielijn voorspelt gemiddelde speeltijd op basis van prijs.\n"

        )
        return result

    except Exception as e:
        return f"Fout bij het uitvoeren van voorspellende analyse: {e}"
