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
from db import get_db_connection, fetch_data_from_db, readplay, readplay_time
import asyncio

playtime = 0  # get from api
limit = 2  # get from db, default = 2, minimum = 0.5?
begin_downtime = 0
end_downtime = 0
current_time = time.time()
steam_id =  int(steamid())
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
    
n = ToastNotifier()

async def alerts():
    global playtime, limit, current_time, n
    while True:
        limit_in_minutes = int(limit) * 60
        if playtime > 0:
            if playtime < int(limit_in_minutes) - 2:
                n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 2 hours of playing left. Don't forget to drink water and stretch", duration=10)
            elif playtime <= int(limit_in_minutes) - 1:
                n.show_toast("Playtime reminder!", f"You have played for {playtime} hours. You have 1 hour of playing left. Don't forget to drink water and stretch", duration=10)
            elif playtime >= int(limit_in_minutes):
                n.show_toast("Playtime is over!", f"You have played for {playtime} hours. You have 0 hours of playing left. Time to drink water and stretch NOW!", duration=10)
        await asyncio.sleep(600)  # Wait for 10 minutes
asyncio.run(alerts())
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
    def refresh_username():
        global username, steam_id
        username = find_username()

    # Navigatieknoppen in de zijbalk
    sidebar_button("Home", lambda: messagebox.showinfo("Actie", "Home")).pack(pady=20, padx=15)
    sidebar_button("Refresh Username", lambda: refresh_username()).pack(pady=20, padx=15)
    sidebar_button("Refetch Playtime", lambda: readplay(steam_id, current_time, playtime, limit, begin_downtime, end_downtime)).pack(pady=20, padx=15)
    sidebar_button("Reload Grafieken", lambda: messagebox.showinfo("Actie", "Instellingen")).pack(pady=20, padx=15)
    
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
                f"Mediaan speeltijd: {beschrijvende_statistieken().split(';')[3]}\n"
                f"Gemiddelde speeltijd: {beschrijvende_statistieken().split(';')[2]}\n"
                f"Playtime: {playtime}\n"
                f"Playtime limiet (in uren): {limit}\n"
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
            "content": "Gebruik AI om voorspellingen te maken over je gemiddelde speeltijd op basis van de prijs.",
            "image_path": "foto.png"  # Replace with the actual path to your image
        },
    ]
    for item in data_grid:
        if "image_path" in item:
            image = Image.open(item["image_path"])
            image = ImageTk.PhotoImage(image)
            item["image"] = image  # Store the image object in the item dictionary
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
                command=lambda: set_limit(entry)
            )
            set_button.pack(pady=10)

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

if __name__ == "__main__":
    main()