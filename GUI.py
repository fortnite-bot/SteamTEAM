import subprocess
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
import time
from datetime import datetime
"""
ideas: 1. Playtime Alerts: gespeeld/ stop en drink water / stretch, check game time, 2. Game Auto-Close: Na X uur, Tussen de uren X en Y, remote access voor ouders (van afstand de game kunnen uitzetten). 3. Email disclosure to selected family members. 
TI: Verander de code uit TI.py om bij zo een alert tijd het rode licht aan te passen (kan met seriele communicatie, mag ook anders) en dan het rode licht uit zetten door de sensor te gebruiken

Filter response for playtime, do calculation for playtime, add to response the playtime, turn neopixel off or on, change that it doesnt turn on by default but only on response and only request response when serial port (or make web api to control game closure and do it from pico and no laptop needed / connect laptop to same api)

gui.py splitsen in verschillende py files, ieder voor zn eigen functies. Pico alle requests en database calls laten handlen. gui.py ook echt alleen de gui zelf hebben. nog een py file voor het sluiten van de apps die connected is aan deze externe api.

Logging: Playtime (api), Username / Steamid, Email van selected family members, settings. (logging betekent sla deze data op in de database)

Notifications: Toast: done

Zorg ervoor dat alle data uit de Steam-API komt en niet uit steam.json

aan de functie AI niet zitten, werkt goed genoeg op het moment. (soms geeft het "sorry ik kan dat niet doen" dus als je dat kan fixen dan sure maar voor de rest niets aanpassen)

de AI data moet ook nog goed uit de json / api gehaald worden en de data dan in dit dashboard

BIM hoeft volgens mij niets in dit dashboard (op ze meest kan je een knop maken met links naar de documenten ofz)

Steam api key van random guy op discord gevonden: ./db.json

Zodat we geen gebruikersnaam hoeven te vragen en lekker origineel blijven, lijkt me een chrome extentie die checkt of je ingelogd bent een handige manier om de steamid te krijgen zonder dat de gebruiker het hoeft in te vullen.

Ander idee: Gebruikersnaam uit systeem halen en dan met chrome extentie de steamid ophalen door de website te openen en gebruiker zijn account te laten kiezen en dan in de database zetten.

https://steamcommunity.com/search/users/#text=yoav
queryselector: .searchPersonaName: href.split('profiles/')[1] of location.href.split('profiles/')[1]

Webserver met api calls als we pico gaan gebruiken als proxy.
76561198081621942
example response:
{"response":{"total_count":8,"games":[{"appid":252950,"name":"Rocket League","playtime_2weeks":485,"playtime_forever":4659,"img_icon_url":"9ad6dd3d173523354385955b5fb2af87639c4163"},{"appid":239160,"name":"Thief","playtime_2weeks":436,"playtime_forever":685,"img_icon_url":"d7688a71380a10c1e6113cee1a25ec8c7ae85aed"},{"appid":577940,"name":"Killer Instinct","playtime_2weeks":225,"playtime_forever":1802,"img_icon_url":"6661bdd76f75fbc0e9692c985f307650971f00e0"},{"appid":438490,"name":"GOD EATER 2 Rage Burst","playtime_2weeks":199,"playtime_forever":238,"img_icon_url":"c694868390c63d40956b78e61dc0df27ce493a8c"},{"appid":489520,"name":"Minion Masters","playtime_2weeks":194,"playtime_forever":44688,"img_icon_url":"ad87d123224d786a413a6021ddaf9257e26c0a28"},{"appid":924970,"name":"Back 4 Blood","playtime_2weeks":152,"playtime_forever":2318,"img_icon_url":"4a2e853e7098bb0ebe637107e8180084a3117184"},{"appid":1971870,"name":"Mortal Kombat 1","playtime_2weeks":147,"playtime_forever":8730,"img_icon_url":"8b1c5aa33466802fc2a5df95505be71fae0b8d47"},{"appid":374400,"name":"VoiceBot","playtime_2weeks":11,"playtime_forever":85,"img_icon_url":"15eb5d42a5542eab826c2d50b1ed31d9b89c5829"}]}}

Yoav: Pure functionaliteit
Walid: Hoe het er uit ziet
Yulisa: Creatieve toepassing
Sharona: AI uitwerken
""" 
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
                "content": "You are given the name of a game, give to the best of your abilities the executable name of that game. only answer with the executablew name. nothing agreeing or outside as this message is going straight into a command prompt. for example if i were to ask for fortnite you would give: FortniteClient-Win64-Shipping.exe. Respond in json format but return it as text, so no markdown {\"response\":{\"executable\": \"FortniteClient-Win64-Shipping.exe\", \"name\": \"Fortnite\"}}" + input_message
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
        response_text = str(data['response']).split('"')[5:6]
        
        return response_text
    except Exception as e:
        print("An error occurred:", str(e))

# Database configuratie
with open("db.json") as f:
    DB_CONFIG = json.load(f)

# Functie om databaseverbinding te maken
retry = False
def get_db_connection():
    global retry
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Fout bij het verbinden met de database: {e}")
        if not retry:
            retry = True 
            return get_db_connection()
        return None

# Functie om gegevens uit de database op te halen
def fetch_data_from_db():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM steam_data")
                rows = cursor.fetchall()
                return rows
        except Exception as e:
            print(f"Fout bij het ophalen van data: {e}")
            return []
        finally:
            conn.close()
    else:
        return []

playtime = 0  # get from api
limit = 2  # get from db, default = 2, minimum = 0.5?
game = ''
begin_downtime = 0
end_downtime = 0
current_time = time.time()
def readplay():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute('SELECT "Playtime", "Playtime_limit", "downtime", "end_downtime", "time" FROM public."User"')
                rows = cursor.fetchall()
                if rows:
                    playtime, limit, begin_downtime, end_downtime, current_time = rows[0]
                else:
                    playtime = 0
                    limit = 2
                    begin_downtime = 0
                    end_downtime = 0
                    current_time = 0
                return playtime, limit, begin_downtime, end_downtime, current_time
        except Exception as e:
            print(f"Fout bij het ophalen van data: {e}")
            return 0, 2, 0, 0, 0
        finally:
            conn.close()
    else:
        return 0, 2, 0, 0, 0

playtime, limit, begin_downtime, end_downtime, current_time = readplay()

if game != '': 
    game = ai(game)[0]

def close_game(game):
    os.system(f'taskkill /f /im {game}')

def find_username():
    global username
    try:
        result = subprocess.run(['powershell.exe', '-Command', 
                                'Get-ItemProperty HKCU:\\Software\\Valve\\Steam\\ -EA 0 | Select-Object AutoLoginUser'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            username = result.stdout.strip().split('-\n')[1]
            print(f"Found Steam username: {username}")
            return username
    
    except Exception as e:
        print(f"Error finding username: {e}")
        return None
    

def alerts():
    global playtime, limit, current_time
    n = ToastNotifier()
    if playtime > 0:
        if playtime < int(limit) - 2: 
            n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 2 hours of playing left. Don't forget to drink water and stretch", duration=10)
        elif playtime < int(limit) - 1:
            n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 1 hour of playing left. Don't forget to drink water and stretch", duration=10)
        elif playtime == int(limit):
            n.show_toast("Playtime is over!", f"You have played for {playtime} hours. You have 0 hours of playing left. Time to drink water and stretch NOW!", duration=10)
            close_game(f'{game}')

        if begin_downtime <= current_time <= end_downtime:
            close_game(f'{game}')

# Dynamisch het bestandspad bepalen
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = fetch_data_from_db()
README_PATH = os.path.join(BASE_DIR, 'README.md')
username = find_username()

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
            text.insert("end", f"Naam: {row[1]}, Prijs: €{row[2]:.2f}, Speeltijd: {row[3]} min, Eigenaren: {row[4]}\n")
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
        IMAGE_PATH = "./voorspellende_analyse_plot.png"
        if os.path.exists(IMAGE_PATH):
            img = Image.open(IMAGE_PATH)
            img = img.resize((600, 300))  # Zonder ANTIALIAS
            img = ImageTk.PhotoImage(img)

            img_label = Label(voorspellende_window, image=img, bg="#9b59b6")
            img_label.image = img  # Houdt de referentie vast
            img_label.pack(pady=20)
        else:
            label = Label(voorspellende_window, text="Afbeelding niet gevonden.", bg="#9b59b6", fg="white")
            label.pack(pady=20)

    except Exception as e:
        print(f"Fout bij het tonen van voorspellende analyse: {e}")

# GUI setup
root = Tk()
root.title("SteamTeam Dashboard")
root.geometry("800x600")  # Increased width for better button placement
root.configure(bg="#2c3e50")

# Frame for layout
frame = Frame(root, bg="#2c3e50", pady=20)
frame.pack(fill="both", expand=True)

center_frame = Frame(frame, bg="#2c3e50", pady=20)
center_frame.pack(expand=True)

# Title Label
label_title = Label(center_frame, text="SteamTeam Dashboard", font=("Helvetica", 24, "bold"), bg="#2c3e50", fg="white", padx=10, pady=10)
label_title.grid(row=0, column=0, columnspan=3, pady=(0, 40))

# Buttons

btn_show_db = Button(
    center_frame,
    text="Bekijk Database Gegevens",
    command=show_database_data,
    bg="#f1c40f",
    fg="white",
    font=("Helvetica", 14),
    relief="solid",
    bd=1,
    padx=20,
    pady=10
)

btn_beschrijvende = Button(
    center_frame,
    text="Beschrijvende Statistieken",
    command=show_beschrijvende_statistieken,
    bg="#1abc9c",
    fg="white",
    font=("Helvetica", 14),
    relief="solid",
    bd=1,
    padx=20,
    pady=10
)

btn_voorspellende = Button(
    center_frame,
    text="Voorspellende Analyse",
    command=show_voorspellende_analyse,
    bg="#9b59b6",
    fg="white",
    font=("Helvetica", 14),
    relief="solid",
    bd=1,
    padx=20,
    pady=10
)

# Arrange buttons in grid with padding
btn_show_db.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
btn_beschrijvende.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
btn_voorspellende.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

# Make the columns expand equally
center_frame.grid_columnconfigure(0, weight=1)
center_frame.grid_columnconfigure(1, weight=1)
center_frame.grid_columnconfigure(2, weight=1)

# Main loop
root.mainloop()

