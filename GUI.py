import subprocess
import os
import json
import pandas as pd
import numpy as np
import psycopg2
from tkinter import Toplevel, Text, Label, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk  # Voor afbeeldingen
from voorspellende import voorspellende_analyse
from win10toast import ToastNotifier
import requests
import time
from datetime import datetime
from steam_memory import steamid
from pcproxy import send
from db import get_db_connection, fetch_data_from_db, readplay, beschrijvende_statistieken, clean_json
import asyncio
import threading
import keyboard


playtime = 0  # get from api
limit = 2  # get from db, default = 2, minimum = 0.5?
begin_downtime = 0
end_downtime = 0
current_time = time.time()
steam_id =  int(steamid())
gemiddelde_speeltijd = 0
median_speeltijd = 0
readplay(steam_id, current_time, playtime, limit, begin_downtime, end_downtime)
send(';2;' + str(playtime) + ';;' + str(limit * 60))

def set_limit(limit_entry):
    global steam_id, current_time, ran, playtime, limit, begin_downtime, end_downtime
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
            playtime, limit, begin_downtime, end_downtime, current_time = readplay(steam_id, current_time, playtime, limit, begin_downtime, end_downtime)


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
    

def alerts():
    n = ToastNotifier()
    global playtime, limit, current_time
    playtime = 3*60
    while True:
        limit_in_minutes = int(limit) * 60
        if playtime > 0:
            if playtime < int(limit_in_minutes) - 2:
                n.show_toast("Playtime reminder!", f"You have played for {playtime // 60} hours. You have 2 hours of playing left. Don't forget to drink water and stretch", duration=10)
            elif playtime <= int(limit_in_minutes) - 1:
                n.show_toast("Playtime reminder!", f"You have played for {playtime // 60} hours. You have 1 hour of playing left. Don't forget to drink water and stretch", duration=10)
            elif playtime >= int(limit_in_minutes):
                n.show_toast("Playtime is over!", f"You have played for {playtime // 60} hours. You have 0 hours of playing left. Time to drink water and stretch NOW!", duration=10)
        time.sleep(600)  # Wait for 10 minutes

# Dynamisch het bestandspad bepalen
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = fetch_data_from_db()
README_PATH = os.path.join(BASE_DIR, 'README.md')
username = find_username()
# Instellen van het thema
ctk.set_appearance_mode("dark")  # Kies tussen "light" en "dark"
ctk.set_default_color_theme("blue")  # Kies een kleurthema (blauw, groen, etc.)

# Kleuren voor het thema
BG_COLOR = "#1F1E1E"  # Zwarte achtergrond voor het hoofdframe
SIDEBAR_COLOR = "#292929"  # Donkergrijs voor de zijbalk
CARD_COLOR = "#404040"  # Lichtere grijs voor de data-kaarten
TEXT_COLOR = "white"  # Witte tekst
ACCENT_COLOR = "#3A8DFF"  # Blauw voor invulelementen (zoals sliders en checkboxes)
BTN_COLOR = "#666666"  # Grijze kleur voor de knoppen
HOVER_BTN_COLOR = "#888888"  # Hover kleur voor de knoppen

def get_friend_details(friend_name):
    # Deze functie zou in werkelijkheid een API-aanroep kunnen zijn die gegevens van Steam haalt.
    # Voor nu gebruiken we fictieve gegevens om het voorbeeld werkend te maken.

    # Fictieve gegevens voor vrienden:
    friend_list = clean_json(beschrijvende_statistieken().split(';;')[3])['friend_list']
    friend_data = {}

    for friend_info in friend_list:
        if ' - Games count: ' in friend_info:
            name_status, games_count = friend_info.rsplit(' - Games count: ', 1)
            name_status_parts = name_status.split(' - ')
            name, status = name_status_parts[0], name_status_parts[1]
            owned_games = [game['name'] for game in clean_json(beschrijvende_statistieken().split(';;')[3])['owned_games'][:5]]
            owned_games = ', '.join(owned_games)
            top_games = clean_json(beschrijvende_statistieken().split(';;')[3])['top_games']
            friend_data[friend_name] = {
                'Username': friend_name,
                "status": status,
                "total_games": int(games_count.split('\'')[0]),
                "owned_games": owned_games,
                "top_games": top_games
            }

    return friend_data.get(friend_name)

def show_friend_details_window(friend_name):
    # Haal vriendgegevens op
    friend_details = get_friend_details(friend_name)
    if not get_friend_details(friend_name):
        messagebox.showerror("Fout", f"Geen gegevens beschikbaar voor {friend_name}")
        return

    # Maak nieuw Toplevel venster
    friend_window = ctk.CTkToplevel()
    friend_window.title(f"Details voor {friend_name}")
    friend_window.geometry("1920x1080")
    friend_window.configure(bg=BG_COLOR)

    # Vrienddetails in het Toplevel venster weergeven
    friend_window_label = ctk.CTkLabel(
        friend_window,
        text=f"Details voor {friend_name}",
        font=("Helvetica", 24, "bold"),
        text_color=ACCENT_COLOR,
        bg_color=BG_COLOR
    )
    friend_window_label.pack(pady=20)

    details_frame = ctk.CTkFrame(friend_window, fg_color=CARD_COLOR, width=460, height=300)
    details_frame.pack(padx=20, pady=20)

    details_text = (
        f"Username: {friend_details['Username']}\n"
        f"Status: {friend_details['status']}\n"
        f"Totaal aantal games: {friend_details['total_games']}\n"
        f"Top games: {friend_details['top_games']}\n"
        f"Owned games: {friend_details['owned_games']}\n"
    )

    friend_details_label = ctk.CTkLabel(
        details_frame,
        text=details_text,
        font=("Helvetica", 14),
        justify="left",
        text_color=TEXT_COLOR,
        bg_color=CARD_COLOR
    )
    friend_details_label.pack(padx=10, pady=10)


def show_dashboard(root):
    global steam_id, current_time, ran, playtime, limit, begin_downtime, end_downtime
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

    # Navigatieknoppen in de zijbalk

    # Middenpaneel voor informatie (data-verdeling)
    content_frame = ctk.CTkFrame(root, fg_color=BG_COLOR)
    content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
    voorspellende_analyse()

    # Data verdeeld over meerdere kaarten in een grid
    data_grid = [
        {
            "title": "Gebruikersstatistieken",
            "content": (
                f"Gebruikersnaam: {find_username()}\n"
                f"Mediaan speeltijd: {beschrijvende_statistieken().split(';;')[2]}\n"
                f"Gemiddelde speeltijd: {beschrijvende_statistieken().split(';;')[1]}\n"
                f"Playtime vandaag: {playtime}\n"
                f"Playtime limiet (in uren): {limit}\n"
                ),
        },
        {
            "title": "Speeltijdlimiet Instellen",
            "content": "Gebruik het veld hieronder om een speeltijdlimiet in te stellen.",
            "interactive": True,
        },
        {
            "title": "Voorspellende Analyse",
            "content": "Gebruik AI om voorspellingen te maken over je gemiddelde speeltijd op basis van de prijs.",
            "image_path": "foto.png"  # Replace with the actual path to your image
        },
        {
            "title": "Vriendenlijst",
            "content": "Klik op een vriend om meer details te zien.",
            "interactive": True,
        }
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

        # Interactieve content voor Speeltijdlimiet en Vriendenlijst
        if item.get("interactive"):
            if item["title"] == "Speeltijdlimiet Instellen":
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
                    command=lambda: set_limit(entry)
                )
                set_button.pack(pady=10)

            elif item["title"] == "Vriendenlijst":
                    #['Van Darkholme (Koen) - Online - Games count: 0', 'Heisenwog (George) (AU) - Offline - Games count: 0', 'Pinoser (NL) - Offline - Games count: 0', 'oevers (NL) - Offline - Games count: 0',  'Jakey - Offline - Games count: 0']

                    friends = beschrijvende_statistieken().split(';;')[3].split(',')  # Fix: Split friends by line
                    for friend_info in friends:
                        if ' - Games count: ' in friend_info:  # Fix: Check if string contains pattern
                            name_status, games_count_info = friend_info.rsplit(' - Games count: ', 1)
                            try:
                                name = name_status.split(' - ')[0].split('[\'')[1]
                            except IndexError:
                                try:
                                    name = name_status.split(' - ')[0].split('\']')[1]
                                except IndexError:
                                    try:
                                        name = name_status.split(' - ')[0].split('\'')[1]
                                    except IndexError:
                                        name = name_status.split(' - ')[0]
                            ctk.CTkButton(
                                card,
                                text=name,
                                font=("Helvetica", 14, "bold"),
                                fg_color=BTN_COLOR,
                                text_color=TEXT_COLOR,
                                hover_color=HOVER_BTN_COLOR,
                                width=200,
                                height=50,
                                corner_radius=10,
                                command=lambda friend=name: show_friend_details_window(friend)
                            ).pack(pady=10, padx=15)

        # Display image if available
        if "image_path" in item:
            image = Image.open(item["image_path"])
            image = image.resize((884, 365))  # Resize the image
            image = ImageTk.PhotoImage(image)
            image_label = ctk.CTkLabel(card, image=image, text="", bg_color=CARD_COLOR)  # Set text to empty
            image_label.image = image  # Keep a reference to avoid garbage collection
            image_label.pack(pady=10)

    # Responsief maken
    content_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_columnconfigure(1, weight=1)
    content_frame.grid_rowconfigure(0, weight=1)
    content_frame.grid_rowconfigure(1, weight=1)


def main():
    root = ctk.CTk()
    root.clear_widgets = lambda: [widget.destroy() for widget in root.winfo_children()]
    root.geometry("1920x1080")
    root.title("SteamTeam Dashboard")
    show_dashboard(root)  # Start met de login scherm
    root.mainloop()


main()