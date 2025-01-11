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
from game import close_game, ai

playtime = 0  # get from api
limit = 2  # get from db, default = 2, minimum = 0.5?
game = ''
begin_downtime = 0
end_downtime = 0
current_time = time.time()
steam_id = int(steamid())
if game != '': 
    game = ai(game)[0]

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