import json
import psycopg2
import time
from steam_memory import steamid
from pcproxy import send
import re

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


ran =  False
response = None
def clean_json(json_str):
    json_str = json_str.replace('\'', "\"")
    return json.loads(re.sub(r'([A-Za-z0-9]+)"([A-Za-z0-9]+)', lambda m: m.group(1) + m.group(2), json_str).replace('True', 'true').replace('False', 'false'), strict=False)
def readplay_time(steam_id, current_time, playtime, limit, begin_downtime, end_downtime): #api --> DB --> Gespeelde tijd binnen een dag
    global ran, response
    if ran: 
        return playtime, limit, begin_downtime, end_downtime, current_time

    # Make request to Steam API
   
    if not isinstance(steam_id, int) or steam_id <= 0:
        steam_id = 0
    responses = send(steam_id).replace("'", "\"")
    response_parts = responses.split(';;;')
    import os; os.system("cls")
    response_parts[2] = str(response_parts[2]).replace(' ()', '')
    
    
    play_time_json = clean_json(response_parts[0])
    player_summary_json = clean_json(response_parts[1])
    friend_list_json = clean_json(response_parts[4])
    owned_games_json = clean_json(response_parts[2])
    top_games = response_parts[3]
    online_status = response_parts[5]
    top_games = owned_games_json[:3]
    result = []
    for i, game in enumerate(top_games, start=1):
        result.append(f"{i}. {game['name']} - {game['playtime_forever'] // 60} uren gespeeld")
    top_games = result   
    response = {
        'play_time': play_time_json,
        'player_summary': player_summary_json,
        'friend_list': friend_list_json,
        'owned_games': owned_games_json,
        'top_games': top_games,
        'online_status': online_status
        }
    

    # Sum playtime_forever
    try:
        total_playtime = sum(game['playtime_forever'] for game in response['play_time']['response']['games'])
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
    ran = True
    return total_playtime_diff
def beschrijvende_statistieken():
    list_playtime = list(game['playtime_forever'] for game in response['play_time']['response']['games'])
    def gemiddelde(data):
        return sum(data) / len(data)
    
    def friendslist():
        if response: 
            return response
# Functie om de mediaan te berekenen
    def mediaan(data):
        sorted_data = sorted(data)  # Sorteer de data
        n = len(sorted_data)
        mid = n // 2                # Vind het midden van de lijst

        if n % 2 == 0: # Als het aantal waarden even is
            return (sorted_data[mid - 1] + sorted_data[mid]) / 2
        else: # Als het aantal waarden oneven is
                return sorted_data[mid]
        
    return f';;{gemiddelde(list_playtime)};;{mediaan(list_playtime)};;{friendslist()}'

def readplay(steam_id, current_time, playtime, limit, begin_downtime, end_downtime): #Set playtime, limit, downtime, end_downtime, current_time from DB
    readplay_time(steam_id, current_time, playtime, limit, begin_downtime, end_downtime)
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