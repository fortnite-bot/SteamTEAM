import os
import json
import pandas as pd
import numpy as np
import psycopg2
from tkinter import Tk, Button, Toplevel, Text, Frame, Label
from PIL import Image, ImageTk
from beschrijvende import beschrijvende_statistieken
from voorspellende import voorspellende_analyse
from win10toast import ToastNotifier
import requests
from datetime import datetime

# Get current time
now = datetime.now()
current_time = now.strftime("%H:%M")

# Database configuration
DB_CONFIG = {
    "dbname": "SteamTeam",
    "user": "postgres",
    "password": "SteamTeam",
    "host": "4.231.88.166",
    "port": 5432,
}

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'steam.json')

# Function to establish database connection
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Fout bij het verbinden met de database: {e}")
        start_db()
        return None

# Function to initialize database
def initialize_database():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
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

# Function to import data into the database
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

# Function to fetch data from the database
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

# Function to show database data
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

# Function to show beschrijvende statistieken
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

# Function to show voorspellende analyse
def show_voorspellende_analyse():
    try:
        voorspellende_resultaten = voorspellende_analyse(DATA_PATH)

        voorspellende_window = Toplevel()
        voorspellende_window.title("Voorspellende Analyse")
        voorspellende_window.geometry("800x600")
        voorspellende_window.configure(bg="#9b59b6")

        # Show textual results
        text = Text(voorspellende_window, wrap="word", bg="#2c3e50", fg="white",
                    font=("Helvetica", 12), padx=10, pady=10, height=10)
        text.insert("1.0", voorspellende_resultaten)
        text.config(state="disabled")
        text.pack(fill="x", padx=10, pady=10)

        # Add image
        IMAGE_PATH = r"C:\\Users\\w_kar\\PycharmProjects\\SteamProject\\voorspellende_analyse_plot.png"
        img = Image.open(IMAGE_PATH)
        img = img.resize((600, 300))  # Without ANTIALIAS
        img = ImageTk.PhotoImage(img)

        img_label = Label(voorspellende_window, image=img, bg="#9b59b6")
        img_label.image = img  # Keep reference
        img_label.pack(pady=20)

    except Exception as e:
        print(f"Fout bij het tonen van voorspellende analyse: {e}")

# Function to close game
def close_game(game):
    os.system(f'taskkill /f /im {game}')

# Function for alerts
def alerts():
    global playtime, limit, current_time
    n = ToastNotifier()
    if playtime < int(limit) - 2:
        n.show_toast("Playtime reminder!",
                     f"You have played for {playtime} hours. You have 2 hours of playing left. Don't forget to drink water and stretch",
                     duration=10)
    elif playtime < int(limit) - 1:
        n.show_toast("Playtime reminder!",
                     f"You have played for {playtime} hours. You have 1 hour of playing left. Don't forget to drink water and stretch",
                     duration=10)
    elif playtime == int(limit):
        n.show_toast("Playtime is over!",
                     f"You have played for {playtime} hours. You have 0 hours of playing left. Time to drink water and stretch NOW!",
                     duration=10)
        close_game(f'{game}')

    if current_time >= begin_downtime and current_time <= end_downtime:
        close_game(f'{game}')

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
label_title = Label(center_frame, text="SteamTeam Dashboard", font=("Helvetica", 24, "bold"), bg="#2c3e50", fg="white",
                    padx=10, pady=10)
label_title.grid(row=0, column=0, columnspan=5, pady=20)

# Buttons
btn_import_data = Button(center_frame, text="Importeer Data naar Database", command=import_data_to_db, bg="#e74c3c",
                         fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_import_data.grid(row=1, column=0, padx=10, pady=10)

btn_show_db = Button(center_frame, text="Bekijk Database Gegevens", command=show_database_data, bg="#f1c40f",
                     fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_show_db.grid(row=1, column=2, padx=10, pady=10)

btn_beschrijvende = Button(center_frame, text="Beschrijvende Statistieken", command=show_beschrijvende_statistieken,
                           bg="#1abc9c", fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_beschrijvende.grid(row=2, column=0, padx=10, pady=10)

btn_voorspellende = Button(center_frame, text="Voorspellende Analyse", command=show_voorspellende_analyse, bg="#9b59b6",
                           fg="white", font=("Helvetica", 14), relief="solid", bd=1, padx=20, pady=10)
btn_voorspellende.grid(row=2, column=2, padx=10, pady=10)

# Database initialization
initialize_database()

# Main loop
root.mainloop()
