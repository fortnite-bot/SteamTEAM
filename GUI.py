import json
import pandas as pd
import numpy as np
import psycopg2
import os
import subprocess
from win10toast import ToastNotifier
import requests
import time
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk  # For images
from beschrijvende import beschrijvende_statistieken
from voorspellende import voorspellende_analyse

# Instellen van het thema
ctk.set_appearance_mode("dark")  # Kies tussen "light" en "dark"
ctk.set_default_color_theme("blue")  # Kies een kleurthema (blauw, groen, etc.)

# Functie om de AI-aanroepen te verwerken (ongewijzigd)
def ai(input_message):
    url = "https://www.promptpal.net/api/chat-gpt-no-stream"
    headers = {'Content-Type': 'application/json'}
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Your prompt here " + input_message}],
        "max_completion_tokens": 128000
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        data = response.json()
        response_text = str(data['response']).split('"')[5:6]
        return response_text
    except Exception as e:
        print("An error occurred:", str(e))

# Database configuratie (ongewijzigd)
with open("db.json") as f:
    DB_CONFIG = json.load(f)

# Functie om verbinding te maken met de database (ongewijzigd)
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

# Functie om gegevens uit de database te halen (ongewijzigd)
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

# Functie om speeltijd uit de database te lezen (ongewijzigd)
def readplay():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    'SELECT "Playtime", "Playtime_limit", "downtime", "end_downtime", "time" FROM public."User"')
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

# Functie om speeltijdlimiet in te stellen (ongewijzigd)
def set_playtime_limit(limit_entry):
    try:
        new_limit = float(limit_entry.get())  # Input in uren
        if new_limit < 0.5:
            raise ValueError("De speeltijdlimiet moet minimaal 0.5 uur zijn.")

        global limit
        limit = new_limit  # Stel de nieuwe limiet in

        print(f"Speeltijdlimiet ingesteld op {limit} uur.")
    except ValueError as e:
        print(f"Fout bij het instellen van de limiet: {e}")

# Functie om een game af te sluiten (ongewijzigd)
def close_game(game):
    os.system(f'taskkill /f /im {game}')

# Functie om gebruikersnaam te vinden (ongewijzigd)
def find_username():
    global username
    try:
        result = subprocess.run(['powershell.exe', '-Command',
                                 'Get-ItemProperty HKCU:\\Software\\Valve\\Steam\\ -EA 0 | Select-Object AutoLoginUser'],
                                capture_output=True, text=True)

        if result.returncode == 0:
            username = result.stdout.strip().split('-\n')[1]
            print(f"Gebruikersnaam van Steam gevonden: {username}")
            return username

    except Exception as e:
        print(f"Fout bij het vinden van de gebruikersnaam: {e}")
        return None

# Functie voor meldingen (ongewijzigd)
def alerts():
    global playtime, limit, current_time
    n = ToastNotifier()
    if playtime > 0:
        if playtime < int(limit) - 2:
            n.show_toast("Speeltijd herinnering!",
                         f"Je hebt {playtime} uur gespeeld. Je hebt 2 uur speeltijd over. Vergeet niet om water te drinken en te rekken.",
                         duration=10)
        elif playtime < int(limit) - 1:
            n.show_toast("Speeltijd herinnering!",
                         f"Je hebt {playtime} uur gespeeld. Je hebt 1 uur speeltijd over. Zorg goed voor je gezondheid.",
                         duration=10)
        elif playtime >= int(limit):
            n.show_toast("Speeltijdlimiet bereikt!",
                         f"Je hebt {playtime} uur gespeeld. Je hebt de speeltijdlimiet bereikt. Overweeg een pauze.",
                         duration=10)
    elif current_time >= end_downtime:
        n.show_toast("Pauze bereikt",
                     "Je hebt je pauze bereikt, neem een break.",
                     duration=10)
    else:
        n.show_toast("Speeltijd herinnering!",
                     f"Je hebt {playtime} uur gespeeld. Speeltijd over: {int(limit) - int(playtime)}",
                     duration=10)

    print("Speeltijd-melding uitgevoerd.")
    return playtime, limit


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SteamTeam Dashboard")
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.state("zoomed")  # Maak het venster opstarten in volledig scherm
        self.frames = {}

        # Configureer het raster om frames volledig uit te rekken
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Voeg frames toe
        self.add_frame(LoginScreen, "LoginScreen")
        self.add_frame(Dashboard, "Dashboard")

        self.show_frame("LoginScreen")

    def add_frame(self, frame_class, name):
        frame = frame_class(parent=self)
        self.frames[name] = frame
        frame.grid(row=0, column=0, sticky="nsew")  # Laat het frame zich uitbreiden in alle richtingen

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()


class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")  # Zorg ervoor dat de achtergrond transparant is

        # Titel
        title = ctk.CTkLabel(
            self,
            text="Welkom bij het SteamTeam!",
            font=("Helvetica", 50),  # Grotere tekstgrootte
            text_color="white",
            fg_color="transparent"
        )
        title.pack(pady=100)  # Vergroot de padding boven en onder de titel

        # Instructie
        instruction = ctk.CTkLabel(
            self,
            text="Voer je Steam ID of gebruikersnaam in:",
            font=("Helvetica", 30),  # Grotere tekstgrootte
            fg_color="transparent",
            text_color="white"
        )
        instruction.pack(pady=40)  # Vergroot de padding boven en onder de instructie

        # Invoerveld
        self.entry = ctk.CTkEntry(
            self,
            font=("Helvetica", 20),  # Grotere tekstgrootte voor invoerveld
            width=400,  # Breder invoerveld
            border_width=2,
            corner_radius=8
        )
        self.entry.pack(pady=30)  # Vergroot de padding boven en onder het invoerveld

        # Login knop
        login_button = ctk.CTkButton(
            self,
            text="Login",
            font=("Helvetica", 20, "bold"),  # Grotere tekstgrootte voor de knop
            fg_color="#4A90E2",
            text_color="white",
            hover_color="#003366",
            width=300,  # Grotere breedte voor de knop
            height=50,  # Grotere hoogte voor de knop
            command=self.validate_login
        )
        login_button.pack(pady=50)  # Vergroot de padding onder de knop

    def validate_login(self):
        steam_id = self.entry.get()
        if steam_id == "12345678":
            self.master.show_frame("Dashboard")
        else:
            messagebox.showerror("Fout", "Ongeldige Steam ID of gebruikersnaam.")


class Dashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")  # Zorg ervoor dat de achtergrond transparant is

        # Titel
        title = ctk.CTkLabel(
            self,
            text="SteamTeam Dashboard",
            font=("Helvetica", 50),  # Grotere tekstgrootte
            text_color="white",
            fg_color="transparent"
        )
        title.pack(pady=100)  # Vergroot de padding boven en onder de titel

        # Beschrijvende secties
        self.create_dashboard_button(
            "Bekijk Database Gegevens",
            lambda: messagebox.showinfo("Actie", "Database Gegevens Weergeven")
        )
        self.create_dashboard_button(
            "Beschrijvende Statistieken",
            lambda: messagebox.showinfo("Actie", "Beschrijvende Statistieken")
        )
        self.create_dashboard_button(
            "Voorspellende Analyse",
            lambda: messagebox.showinfo("Actie", "Voorspellende Analyse")
        )

        # Speeltijdlimiet
        limit_label = ctk.CTkLabel(
            self,
            text="Stel speeltijdlimiet in (in uren):",
            font=("Helvetica", 30),  # Grotere tekstgrootte
            fg_color="transparent",
            text_color="white"
        )
        limit_label.pack(pady=40)  # Vergroot de padding boven en onder het label

        limit_entry = ctk.CTkEntry(
            self,
            font=("Helvetica", 20),  # Grotere tekstgrootte voor invoerveld
            width=400,  # Breder invoerveld
            border_width=2,
            corner_radius=8
        )
        limit_entry.pack(pady=30)  # Vergroot de padding boven en onder het invoerveld

        set_limit_button = ctk.CTkButton(
            self,
            text="Instellen",
            font=("Helvetica", 20, "bold"),  # Grotere tekstgrootte voor de knop
            fg_color="#4A90E2",
            text_color="white",
            hover_color="#003366",
            width=300,  # Grotere breedte voor de knop
            height=50,  # Grotere hoogte voor de knop
            command=lambda: messagebox.showinfo("Limiet", f"Limiet ingesteld: {limit_entry.get()} uur")
        )
        set_limit_button.pack(pady=50)  # Vergroot de padding onder de knop

    def create_dashboard_button(self, text, command):
        button = ctk.CTkButton(
            self,
            text=text,
            font=("Helvetica", 20),  # Grotere tekstgrootte voor knoppen
            fg_color="#4A90E2",
            text_color="white",
            hover_color="#003366",
            width=400,  # Brede knoppen
            height=50,  # Hogere knoppen
            command=command
        )
        button.pack(pady=20)  # Vergroot de padding boven en onder de knoppen


# Start de applicatie
if __name__ == "__main__":
    app = App()
    app.mainloop()

