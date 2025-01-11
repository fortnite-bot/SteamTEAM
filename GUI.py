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

with open("db.json") as f:
    DB_CONFIG = json.load(f)

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
            print(f"Gebruikersnaam van Steam gevonden: {username}")
            return username

    except Exception as e:
        print(f"Fout bij het vinden van de gebruikersnaam: {e}")
        return None

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

# Kleuren voor het thema
BG_COLOR = "#1F1E1E"  # Zwarte achtergrond voor het hoofdframe
SIDEBAR_COLOR = "#292929"  # Donkergrijs voor de zijbalk
CARD_COLOR = "#404040"  # Lichtere grijs voor de data-kaarten
TEXT_COLOR = "white"  # Witte tekst
ACCENT_COLOR = "#3A8DFF"  # Blauw voor invulelementen (zoals sliders en checkboxes)
BTN_COLOR = "#666666"  # Grijze kleur voor de knoppen
HOVER_BTN_COLOR = "#888888"  # Hover kleur voor de knoppen

def show_login_screen(root):
    root.clear_widgets()

    def validate_login():
        steam_id = entry.get()
        if steam_id == "12345678":  # Je kunt hier je eigen login-logic implementeren
            show_dashboard(root)
        else:
            messagebox.showerror("Fout", "Ongeldige Steam ID of gebruikersnaam.")

    title = ctk.CTkLabel(root, text="Welkom bij het SteamTeam!", font=("Helvetica", 50), text_color="white")
    title.pack(pady=100)

    instruction = ctk.CTkLabel(root, text="Voer je Steam ID of gebruikersnaam in:", font=("Helvetica", 30), text_color="white")
    instruction.pack(pady=40)

    entry = ctk.CTkEntry(root, font=("Helvetica", 20), width=400, border_width=2, corner_radius=8)
    entry.pack(pady=30)

    login_button = ctk.CTkButton(root, text="Login", font=("Helvetica", 20, "bold"), fg_color="#4A90E2", text_color="white", hover_color="#003366", width=300, height=50, command=validate_login)
    login_button.pack(pady=50)

def show_dashboard(root):
    root.clear_widgets()

    root.configure(bg=BG_COLOR)

    # Titelbalk bovenaan
    title_frame = ctk.CTkFrame(root, height=80, corner_radius=0, fg_color=CARD_COLOR)
    title_frame.pack(side="top", fill="x")

    title_label = ctk.CTkLabel(
        title_frame,
        text="SteamTeam Dashboard",
        font=("Helvetica", 36, "bold"),
        text_color=ACCENT_COLOR,
        bg_color=CARD_COLOR
    )
    title_label.pack(pady=20)

    # Zijbalk links
    sidebar_frame = ctk.CTkFrame(root, width=250, fg_color=SIDEBAR_COLOR)
    sidebar_frame.pack(side="left", fill="y")

    def sidebar_button(text, command):
        return ctk.CTkButton(
            sidebar_frame,
            text=text,
            font=("Helvetica", 14, "bold"),
            fg_color=BTN_COLOR,
            text_color=TEXT_COLOR,
            hover_color=HOVER_BTN_COLOR,
            width=200,
            height=50,
            corner_radius=10,
            command=command
        )

    # Navigatieknoppen in de zijbalk
    sidebar_button("Home", lambda: messagebox.showinfo("Actie", "Home")).pack(pady=20, padx=15)
    sidebar_button("Statistieken", lambda: messagebox.showinfo("Actie", "Statistieken")).pack(pady=20, padx=15)
    sidebar_button("Analyse", lambda: messagebox.showinfo("Actie", "Analyse")).pack(pady=20, padx=15)
    sidebar_button("Instellingen", lambda: messagebox.showinfo("Actie", "Instellingen")).pack(pady=20, padx=15)

    # Middenpaneel voor informatie (data-verdeling)
    content_frame = ctk.CTkFrame(root, fg_color=BG_COLOR)
    content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    # Data verdeeld over meerdere kaarten in een grid
    data_grid = [
        {
            "title": "Gebruikersstatistieken",
            "content": (
                "Gebruikersnaam: [Placeholder]\n"
                "Status: Offline\n"
                "Mediaan speeltijd: N/A\n"
                "Gemiddelde speeltijd: N/A\n"
                "Laatste 2 weken speeltijd: N/A"
            ),
        },
        {
            "title": "Speeltijdlimiet Instellen",
            "content": "Gebruik het veld hieronder om een speeltijdlimiet in te stellen.",
            "interactive": True,
        },
        {
            "title": "Grafieken & Analyse",
            "content": "Hier komen grafieken en visualisaties van je speeltijd.",
        },
        {
            "title": "Voorspellende Analyse",
            "content": "Gebruik AI om voorspellingen te maken over je speeltijd en gedrag.",
        },
    ]

    for i, item in enumerate(data_grid):
        card = ctk.CTkFrame(content_frame, width=400, height=250, fg_color=CARD_COLOR, corner_radius=15)
        card.grid(row=i // 2, column=i % 2, padx=20, pady=20, sticky="nsew")

        # Titel van de kaart
        card_title = ctk.CTkLabel(
            card,
            text=item["title"],
            font=("Helvetica", 18, "bold"),
            text_color=ACCENT_COLOR,
            bg_color=CARD_COLOR
        )
        card_title.pack(anchor="w", pady=10, padx=15)

        # Content van de kaart
        card_content = ctk.CTkLabel(
            card,
            text=item["content"],
            font=("Helvetica", 14),
            justify="left",
            text_color=TEXT_COLOR,
            bg_color=CARD_COLOR
        )
        card_content.pack(anchor="w", pady=5, padx=15)

        # Interactieve content voor speeltijdlimiet
        if item.get("interactive"):
            entry = ctk.CTkEntry(card, font=("Helvetica", 14), width=300, corner_radius=8)
            entry.pack(pady=10)

            set_button = ctk.CTkButton(
                card,
                text="Instellen",
                font=("Helvetica", 14, "bold"),
                fg_color=BTN_COLOR,
                text_color=TEXT_COLOR,
                hover_color=HOVER_BTN_COLOR,
                width=150,
                height=40,
                corner_radius=10,
                command=lambda: set_playtime_limit(entry)
            )
            set_button.pack(pady=10)

    # Responsief maken
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_columnconfigure(1, weight=1)
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_rowconfigure(1, weight=1)

def set_playtime_limit(entry):
    try:
        new_limit = float(entry.get())  # Input in uren
        if new_limit < 0.5:
            raise ValueError("De speeltijdlimiet moet minimaal 0.5 uur zijn.")
        print(f"Nieuwe speeltijdlimiet ingesteld op: {new_limit} uur.")
    except ValueError as e:
        messagebox.showerror("Fout", str(e))

def main():
    root = ctk.CTk()
    root.clear_widgets = lambda: [widget.destroy() for widget in root.winfo_children()]
    root.geometry("1920x1080")
    root.title("SteamTeam Dashboard")
    show_login_screen(root)  # Start met de login scherm
    root.mainloop()

if __name__ == "__main__":
    main()