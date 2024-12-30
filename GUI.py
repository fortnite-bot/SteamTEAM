import os
import json
import pandas as pd
import numpy as np
import psycopg2
from tkinter import Tk, Button, Toplevel, Text, Scrollbar, RIGHT, Y, VERTICAL, Frame, Label
from PIL import Image, ImageTk  # Voor afbeeldingen
from beschrijvende import beschrijvende_statistieken
from voorspellende import voorspellende_analyse
from win10toast import ToastNotifier
import requests
from datetime import datetime
import ctypes

now = datetime.now()

current_time = now.strftime("%H:%M")
"""
ideas: 1. Playtime Alerts: gespeeld/ stop en drink water / stretch, check game time, check process launch, 2. Game Auto-Close: Na X uur, Tussen de uren X en Y, remote access voor ouders (van afstand de game kunnen uitzetten). 3. Email disclosure to selected family members. 

Logging: Playtime (local + api), Username / Steamid, Email van selected family members, settings.

Notifications: Toast

Username / Steamid: Memory read: "steam.exe"+0009D1D0, offset: 1C
""" 

def read_username():
#nog idee nodig op hoe we dit gaan doen
#iteratie over ieder memory address 
    import pymeow as pm
    import time

    def find_string_in_memory(target_string):
        process = pm.process_by_name("steam.exe")
        
        if not process:
            print("Steam.exe not found!")
            return None
        
        address = 0
        start_time = time.time()
        
        while True:
            data = process.read_bytes(address, 4096)
            
            if target_string in data.decode('utf-8', errors='ignore'):
                print(f"Found '{target_string}' at address: {address}")
                return address
            
            address += 4096
            
            if time.time() > start_time + 60:
                break
        
        print("Target string not found within the scanned memory.")
        return None

    # Usage example
    target_string = "Account Details:"
    result = find_string_in_memory(target_string)


def start_db():
    # Set up session with custom user agent
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})

    # First request to get token
    token_url = "https://login.microsoftonline.com/98932909-9a5a-4d18-ace4-7236b5b5e11d/oauth2/v2.0/token"
    data = {
        "client_id": "c44b4083-3bb0-49c1-b47d-974e53cbdf3c",
        "scope": "openid profile offline_access",
        "code": "1.AQIACSmTmFqaGE2s5HI2tbXhHYNAS8SwO8FJtH2XTlPL3zwCAJcCAA.AgABBAIAAADW6jl31mB3T7ugrWTT8pFeAwDs_wUA9P8Lxrffir5eU1jYrZTsLVNhp3IhICIRE6_IhEh_Ox5JG420NJchQvYsiBEIPEAHQhrKf8BbTYa615E8Bn9YnmXgbRanEUhHw5cpm7ahiw5symPkUrlVeVOUS1eM-YOhIzXRPRuPhH3hxLVP5rHIfSp120koqA0rqgsgLcLavYVzZYKLW9ORgsvkHUcZRskqe5s3nclv7ziLd2zk0bLkQhsZ0Y32km9adT1VpnTJHr7qfarFoaDMBzysRN6VbOYDD4yH5jPmP2X6ggM7huw82vSwR3vCcTSOzNM4-eNO9NVIJgU-6XVz1l6YtBz-DsdSjCacQHgHNG3IOPvWAcTX8OLIIqafWJMD-6f1S_HAfJGgg8kKSfwLsusYin5zuQUnx1JlgB4EV6vmELYlHDCRm_PBbmOXwLbl0OKFVZmgNEN-NEOCEzt4G2Ci_JdkGFtBVxSauoSyLpMN1ykP8qkPImLB-H8MNLMpPv_o_cs8-neIOjWdstO-FUSvMokKd-yWmk8Td91CH5dc7C4E-A_82NAwfKZO5qu1GFZDCyPmatKcIqkGWhoFSCljGnI7zsRMf4dr5xdkU0-I9fZm75oFYfmYzWm948qKJ_ry0ZY1KdmAhJBMWpSNQJPv6WPPo2kF3Wjpdx7j29l6QvXZR7ge9l4tHuyxrd8IhkkbAWjELvK6wCTaK1FZmjzf5dSk0aW2BT1oeCPLNWHUHz-7JcKbGrFlWhI3BXbUlXK6oNyfEpLQSk5KN64QEnw",
        "x-client-SKU": "msal.js.browser",
        "x-client-VER": "2.37.0",
        "x-ms-lib-capability": "retry-after, h429",
        "x-client-current-telemetry": "5|866,0,,,,||,|&",
        "x-client-last-telemetry": "5||0||0,0",
        "grant_type": "authorization_code",
        "client_info": "1",
        "client-request-id": "b0c0589c-5887-4a08-a142-4ba6551245bb"
    }

    response = session.post(token_url, data=data)

    # Extract token from response
    access_token = response.json()['access_token']
    refresh_token = response.json()['refresh_token']

    # Second request to start VM
    start_vm_url = "https://management.azure.com/subscriptions/3423a52d-b680-4bea-901b-1317e5a45bb1/resourceGroups/SteamTeam/providers/Microsoft.Compute/virtualMachines/SteamTeam-DB-HST/start?api-version=2024-03-01"

    headers = {
        "x-ms-client-session-id": "06900540aaaa49e68e27e201ba6c879e",
        "Authorization": f"Bearer {access_token}"
    }

    response = session.post(start_vm_url, headers=headers)

def ai(input_message):
     # Prompt the user for input
    
    # Set up the API request
    url = "https://www.promptpal.net/api/chat-gpt-no-stream"
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {
                "role": "user",
                "content": "You are given the name of a game, give to the best of your abilities the executable name of that game. only answer with the executablew name. nothing agreeing or outside as this message is going straight into a command prompt. for example if i were to ask for fortnite you would give: FortniteClient-Win64-Shipping.exe:" + input_message
            }
        ],
        "max_completion_tokens": 128000
    }

    try:
        # Send the POST request
        response = requests.post(url, headers=headers, json=data)
        
        # Check if the request was successful
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Extract and log the response text
        response_text = data.get('response', '')
        if not str(response_text).endswith('.exe'):
            return 'null.exe'
        return response_text
    except requests.exceptions.RequestException as e:
        print("An error occurred:", str(e))

playtime = 0 #get from api
limit = 2 #get from db, default = 2, minimum = 0.5?
game = ''
begin_downtime = 0
end_downtime = 0
if game != '': 
    game = ai(game)
 
def close_game(game):
    os.system(f'taskkill /f /im {game}')

def alerts():
    
    global playtime, limit, current_time
    n = ToastNotifier()
    if playtime < int(limit) - 2: 
        n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 2 hours of playing left. Dont forget to drink water and stretch", duration = 10)
    elif playtime < int(limit) - 1:
        n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 1 hour of playing left. Dont forget to drink water and stretch", duration = 10)
    elif playtime == int(limit):
        n.show_toast("Playtime is over!", f"You have played for {playtime} hours. You have 0 hours of playing left. Time to drink water and stretch NOW!", duration = 10)
        close_game(f'{game}')
    
    if current_time >= begin_downtime and current_time <= end_downtime:
            close_game(f'{game}')

alerts()
# Database configuratie
DB_CONFIG = {
    "dbname": "SteamTeam",
    "user": "postgres",
    "password": "SteamTeam",
    "host": "4.231.88.166",
    "port": 5432,
}

# Dynamisch het bestandspad bepalen
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'steam.json')
README_PATH = os.path.join(BASE_DIR, 'README.md')

# Controleer of de vereiste bestanden bestaan
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Data bestand niet gevonden: {DATA_PATH}")
if not os.path.exists(README_PATH):
    raise FileNotFoundError(f"README.md bestand niet gevonden: {README_PATH}")

# Functie om databaseverbinding te maken
retry = False
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Fout bij het verbinden met de database: {e}")
        start_db()
        if not retry:
            retry = True 
            get_db_connection()
        return None

# Functie om de database voor te bereiden
def initialize_database():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                # Maak tabel als deze nog niet bestaat
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS steam_data (
                        id SERIAL PRIMARY KEY,
                        name TEXT,
                        price FLOAT,
                        average_playtime INT,
                        owners TEXT
                    )
                """)
                conn.commit()
                print("Database succesvol geïnitialiseerd.")
        except Exception as e:
            print(f"Fout bij het initialiseren van de database: {e}")
        finally:
            conn.close()

# Functie om gegevens naar de database te importeren
def import_data_to_db():
    conn = get_db_connection()
    if conn:
        try:
            with open(DATA_PATH, 'r') as file:
                data = json.load(file)

            with conn.cursor() as cursor:
                for game in data:
                    cursor.execute("""
                        INSERT INTO steam_data (name, price, average_playtime, owners)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        game.get('name', 'Onbekend'),
                        game.get('price', 0.0),
                        game.get('average_playtime', 0),
                        game.get('owners', 'Onbekend')
                    ))
                conn.commit()
                print("Data succesvol geïmporteerd in de database.")
        except Exception as e:
            print(f"Fout bij het importeren van data: {e}")
        finally:
            conn.close()

# Functie om gegevens uit de database op te halen
def fetch_data_from_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT name, price, average_playtime, owners FROM steam_data")
                rows = cursor.fetchall()
                return rows
        except Exception as e:
            print(f"Fout bij het ophalen van data: {e}")
            return []
        finally:
            conn.close()

# Functie om databasegegevens te tonen
def show_database_data():
    data = fetch_data_from_db()

    db_window = Toplevel()
    db_window.title("Steam Database Gegevens")
    db_window.geometry("800x600")
    db_window.configure(bg="#34495e")

    text = Text(db_window, wrap="word", bg="#2c3e50", fg="white", font=("Helvetica", 12), padx=10, pady=10)
    if data:
        for row in data:
            text.insert("end", f"Naam: {row[0]}, Prijs: €{row[1]:.2f}, Speeltijd: {row[2]} min, Eigenaren: {row[3]}\n")
    else:
        text.insert("end", "Geen gegevens gevonden in de database.")
    text.config(state="disabled")
    text.pack(fill="both", expand=True)

# Functie om beschrijvende statistieken te tonen
def show_beschrijvende_statistieken():
    try:
        beschrijvende_resultaten = beschrijvende_statistieken(DATA_PATH)

        beschrijvende_window = Toplevel()
        beschrijvende_window.title("Beschrijvende Statistieken")
        beschrijvende_window.geometry("800x400")
        beschrijvende_window.configure(bg="#1abc9c")

        text = Text(beschrijvende_window, wrap="word", bg="#2c3e50", fg="white", font=("Helvetica", 12), padx=10, pady=10)
        text.insert("1.0", beschrijvende_resultaten)
        text.config(state="disabled")
        text.pack(fill="both", expand=True)
    except Exception as e:
        print(f"Fout bij het tonen van beschrijvende statistieken: {e}")

# Functie om voorspellende analyse te tonen
def show_voorspellende_analyse():
    try:
        voorspellende_resultaten = voorspellende_analyse(DATA_PATH)

        voorspellende_window = Toplevel()
        voorspellende_window.title("Voorspellende Analyse")
        voorspellende_window.geometry("800x600")
        voorspellende_window.configure(bg="#9b59b6")

        # Toon de tekstuele resultaten
        text = Text(voorspellende_window, wrap="word", bg="#2c3e50", fg="white",
                    font=("Helvetica", 12), padx=10, pady=10, height=10)
        text.insert("1.0", voorspellende_resultaten)
        text.config(state="disabled")
        text.pack(fill="x", padx=10, pady=10)

        # Voeg de afbeelding toe
        IMAGE_PATH = r"C:\\Users\\w_kar\\PycharmProjects\\SteamProject\\voorspellende_analyse_plot.png"
        img = Image.open(IMAGE_PATH)
        img = img.resize((600, 300))  # Zonder ANTIALIAS
        img = ImageTk.PhotoImage(img)

        img_label = Label(voorspellende_window, image=img, bg="#9b59b6")
        img_label.image = img  # Houdt de referentie vast
        img_label.pack(pady=20)

    except Exception as e:
        print(f"Fout bij het tonen van voorspellende analyse: {e}")

# GUI setup
root = Tk()
root.title("SteamTeam Dashboard")
root.geometry("700x600")
root.configure(bg="#2c3e50")

# Frame for layout
frame = Frame(root, bg="#2c3e50", pady=20)
frame.pack(fill="both", expand=True)

center_frame = Frame(frame, bg="#2c3e50", pady=20)
center_frame.pack(expand=True)

# Title Label
label_title = Label(center_frame, text="SteamTeam Dashboard", font=("Helvetica", 24, "bold"), bg="#2c3e50", fg="white", padx=10, pady=10)
label_title.grid(row=0, column=0, columnspan=5, pady=20)

# Buttons
btn_import_data = Button(center_frame, text="Importeer Data naar Database", command=import_data_to_db, bg="#e74c3c", fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_import_data.grid(row=1, column=0, padx=10, pady=10)

btn_show_db = Button(center_frame, text="Bekijk Database Gegevens", command=show_database_data, bg="#f1c40f", fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_show_db.grid(row=1, column=2, padx=10, pady=10)

btn_beschrijvende = Button(center_frame, text="Beschrijvende Statistieken", command=show_beschrijvende_statistieken, bg="#1abc9c", fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_beschrijvende.grid(row=2, column=0, padx=10, pady=10)

btn_voorspellende = Button(center_frame, text="Voorspellende Analyse", command=show_voorspellende_analyse, bg="#9b59b6", fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_voorspellende.grid(row=2, column=2, padx=10, pady=10)

# Database initialisatie
initialize_database()

# Main loop
root.mainloop()
