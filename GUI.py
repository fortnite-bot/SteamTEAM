import subprocess
import os
import json
import pandas as pd
import numpy as np
import psycopg2
from tkinter import Toplevel, Text, Label, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk  # Voor afbeeldingen
from beschrijvende import beschrijvende_statistieken
from voorspellende import voorspellende_analyse
from win10toast import ToastNotifier
import requests
import time
from datetime import datetime
from steam_memory import steamid
from pcproxy import send

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
with open("../db.json", encoding="utf-8") as f:
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
steam_id = int(steamid())

def readplay_time(): #api --> DB --> Gespeelde tijd binnen een dag
    global steam_id, current_time
    with open('steamkey.json', 'r') as file:
        data = json.load(file)
        steam_key = data['steamkey']

    # Make request to Steam API
   
    if not isinstance(steam_id, int) or steam_id <= 0:
        steam_id = 0
    response = send(steam_id).replace("'", "\"").replace("\"s", "s")	
    response = json.loads(response, strict=False)


    # Sum playtime_forever
    try:
        total_playtime = sum(game['playtime_forever'] for game in response['response']['games'])
        # Get the current playtime from the database for the specific user
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT \"Playtime\" FROM public.\"User\" WHERE \"User\" = %s ORDER BY \"time\" DESC LIMIT 1", (str(steam_id),))
        last_playtime_entry = cursor.fetchone()

        # Check if the playtime has changed
        if last_playtime_entry is None or total_playtime != int(last_playtime_entry[0]):
            # Insert total playtime into database
            cursor.execute("INSERT INTO public.\"User\" (\"User\",\"Playtime\", \"time\") VALUES (%s, %s, %s)", (str(steam_id), str(total_playtime), current_time))
            conn.commit()

        # Query for entries in the past 24 hours for the specific user
        past_24_hours = current_time - 86400
        cursor.execute("SELECT \"time\", \"Playtime\" FROM public.\"User\" WHERE \"User\" = %s AND \"time\" BETWEEN %s AND %s", (str(steam_id), past_24_hours, current_time))
        recent_rows = cursor.fetchall()

        # Calculate differences
        total_playtime_diff = 0
        for row in recent_rows:
            playtime_diff = total_playtime - int(row[1])
            total_playtime_diff += playtime_diff

        # Close the database connection
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        total_playtime = 0
        total_playtime_diff = 0
    return total_playtime_diff
def readplay(): #Set playtime, limit, downtime, end_downtime, current_time from DB
    readplay_time()
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
    
def set_limit(limit_entry):
    global steam_id
    limit = limit_entry.get()
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE public.\"User\" SET \"Playtime_limit\" = %s WHERE \"User\" = %s", (limit, str(steam_id)))
                conn.commit()
        except Exception as e:
            print(f"Fout bij het updaten van de limiet: {e}")
        finally:
            conn.close()
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
            output_lines = result.stdout.strip().split('-\n')
            if len(output_lines) > 1:
                username = output_lines[1].strip()
            else:
                username = None
            print(f"Found Steam username: {username}")
            return username
    
    except Exception as e:
        print(f"Error finding username: {e}")
        return None
    
n = ToastNotifier()

def alerts():
    global playtime, limit, current_time, game, n
    limit = int(limit) * 60
    send(';2;'+str(playtime)+';;'+str(limit))
    if playtime > 0:
        if playtime < int(limit) - 2: 
            n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 2 hours of playing left. Don't forget to drink water and stretch", duration=10)
        elif playtime <= int(limit) - 1:
            n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 1 hour of playing left. Don't forget to drink water and stretch", duration=10)
        elif playtime >= int(limit):
            n.show_toast("Playtime is over!", f"You have played for {playtime} hours. You have 0 hours of playing left. Time to drink water and stretch NOW!", duration=10)
            close_game(game)

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


# Instellen van het thema
ctk.set_appearance_mode("dark")  # Kies tussen "light" en "dark"
ctk.set_default_color_theme("blue")  # Kies een kleurthema (blauw, groen, etc.)

def show_dashboard(root):
    root.clear_widgets()

    def create_dashboard_button(text, command):
        button = ctk.CTkButton(root, text=text, font=("Helvetica", 20), fg_color="#4A90E2", text_color="white", hover_color="#003366", width=400, height=50, command=command)
        button.pack(pady=20)

    title = ctk.CTkLabel(root, text="SteamTeam Dashboard", font=("Helvetica", 50), text_color="white")
    title.pack(pady=100)

    create_dashboard_button("Bekijk Database Gegevens", lambda: messagebox.showinfo("Actie", "Database Gegevens Weergeven"))
    create_dashboard_button("Beschrijvende Statistieken", lambda: messagebox.showinfo("Actie", "Beschrijvende Statistieken"))
    create_dashboard_button("Voorspellende Analyse", lambda: messagebox.showinfo("Actie", "Voorspellende Analyse"))

    limit_label = ctk.CTkLabel(root, text="Stel speeltijdlimiet in (in uren):", font=("Helvetica", 30), text_color="white")
    limit_label.pack(pady=40)

    limit_entry = ctk.CTkEntry(root, font=("Helvetica", 20), width=400, border_width=2, corner_radius=8)
    limit_entry.pack(pady=30)

    set_limit_button = ctk.CTkButton(root, text="Instellen", font=("Helvetica", 20, "bold"), fg_color="#4A90E2", text_color="white", hover_color="#003366", width=300, height=50, command=lambda: set_limit(limit_entry))
    set_limit_button.pack(pady=50)

def main():
    root = ctk.CTk()
    root.clear_widgets = lambda: [widget.destroy() for widget in root.winfo_children()]
    root.geometry("1920x1080")
    root.title("SteamTeam Dashboard")
    show_dashboard(root)
    root.mainloop()
main()