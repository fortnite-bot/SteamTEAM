import requests
import numpy as np
import matplotlib.pyplot as plt

# De API-link en parameters
url = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/"
params = {
    "key": "281C1716E751A37C4A73A7AAF53ADA1D",  # Jouw API-sleutel
    "steamid": "76561198081621942"  # Steam ID
}

# Data ophalen
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    if "response" in data and "games" in data["response"]:
        games = data["response"]["games"]

        # Haal speeltijden op
        playtimes = [game["playtime_forever"] for game in games]
        indices = list(range(1, len(playtimes) + 1))  # Gebruik game-index als x

        # Omzetten naar numpy arrays
        X = np.array(indices).reshape(-1, 1)  # Kenmerken (game-index)
        y = np.array(playtimes)  # Doelen (speeltijden)

        # Normaliseer de data
        X_norm = (X - np.mean(X)) / np.std(X)
        y_norm = (y - np.mean(y)) / np.std(y)

        # Parameters initialiseren
        theta_0 = 0  # Bias
        theta_1 = 0  # Helling
        alpha = 0.01  # Leerwaarde
        epochs = 1000  # Aantal iteraties
        m = len(y)  # Aantal trainingsvoorbeelden

        # Gradient descent
        for _ in range(epochs):
            # Voorspelling
            y_pred_norm = theta_0 + theta_1 * X_norm.flatten()

            # Bereken de gradiënten
            d_theta_0 = (1 / m) * np.sum(y_pred_norm - y_norm)
            d_theta_1 = (1 / m) * np.sum((y_pred_norm - y_norm) * X_norm.flatten())

            # Update parameters
            theta_0 -= alpha * d_theta_0
            theta_1 -= alpha * d_theta_1

        # Denormaliseer de parameters (voor echte speeltijdvoorspellingen)
        y_mean = np.mean(playtimes)
        y_std = np.std(playtimes)
        theta_0_denorm = theta_0 * y_std + y_mean
        theta_1_denorm = theta_1 * y_std

        # Voorspellen voor de bestaande games
        predicted_playtimes = theta_0_denorm + theta_1_denorm * X.flatten()

        # Zet de tijden om naar uren (delen door 60)
        playtimes_hours = np.array(playtimes) / 60
        predicted_playtimes_hours = predicted_playtimes / 60

        # Voorspellen voor toekomstige games (bijvoorbeeld game 9, 10, 11, 12, 13)
        future_indices = [9, 10, 11, 12, 13]
        future_indices_normalized = (np.array(future_indices) - np.mean(indices)) / np.std(indices)
        future_predictions = theta_0_denorm + theta_1_denorm * future_indices_normalized

        # Zet de voorspellingen om naar uren
        future_predictions_hours = future_predictions / 60

        # Print de voorspelde gemiddelde speeltijd voor de toekomstige games
        for i, pred in zip(future_indices, future_predictions_hours):
            print(f"Voorspelde gemiddelde speeltijd voor game {i}: {pred:.2f} uur")

        # Plot de gegevens en de regressielijn in uren
        plt.figure(figsize=(10, 6))

        # Plot alleen de voorspellingen voor games 9 t/m 13
        plt.plot(future_indices, future_predictions_hours, color="red", label="Voorspelde regressielijn (uren)",
                 linewidth=2)

        # Voeg voorspelde speeltijden voor toekomstige games toe als aparte punten
        plt.scatter(future_indices, future_predictions_hours, color="green", label="Voorspelde speeltijden (uren)",
                    zorder=5)

        # Titels en labels
        plt.title("Voorspelde speeltijden (in uren) voor toekomstige games")
        plt.xlabel("Game index")
        plt.ylabel("Speeltijd (uren)")
        plt.legend()
        plt.grid(True)
        plt.show()



