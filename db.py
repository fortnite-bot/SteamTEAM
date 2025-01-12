import json
import psycopg2
import time
from steam_memory import steamid
from pcproxy import send

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
def readplay_time(steam_id, current_time, playtime, limit, begin_downtime, end_downtime): #api --> DB --> Gespeelde tijd binnen een dag
    global ran
    if ran: 
        return playtime, limit, begin_downtime, end_downtime, current_time

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
    ran = True
    return total_playtime_diff
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