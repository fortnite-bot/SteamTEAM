import machine
import time
import neopixel
import network
import urequests
import json
import uasyncio as asyncio
import _thread
import datetime

# Initialize command list
commands = []

# Initialize hardware
TRIG_PIN = 17     # GPIO5
ECHO_PIN = 16    # GPIO18
NUM_LEDS = 8         # Number of LEDs in the strip
LED_PIN = 18          # GPIO4 (commonly used for NeoPixels)
DETECTION_DISTANCE = 15    # Distance in centimeters to trigger the LEDs
DEBOUNCE_TIME = 0        # Seconds to wait before re-detecting

trig = machine.Pin(TRIG_PIN, machine.Pin.OUT)
echo = machine.Pin(ECHO_PIN, machine.Pin.IN)
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)
with open('steamkey.json', 'r') as file:
    data = json.load(file)
    steam_key = data['steamkey']
# Function to read play time from Steam API
def steam_api_functions(steam_id):
    global steam_key

    def play_time(steam_id):
        url = f'https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v1/?key={steam_key}&steamid={steam_id}'
        response = urequests.get(url).json()
        return(response)

    def player_summary(steam_id):
        url = f'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/'
        params = {
            'key': steam_key,
            'steamids': steam_id
        }
        response = urequests.get(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
        return response.json()
    game_count = 0 
    def owned_games():
        url = f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/'
        params = {
            'key': steam_key,
            'steamid': steam_id,
            'include_appinfo': True,
            'format': 'json'
        }
        print(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()]))
        response = urequests.get(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])).json()
        response = json.loads(response)
        if 'response' in response and 'games' in response['response']:
            played_games = response['response']['games']
            global game_count 
            game_count = response['response']['game_count']
            return played_games
        return []

    def top_games(top_n=5):
        played_games = owned_games()
        top_games = played_games[:top_n]
        result = []
        for i, game in enumerate(top_games, start=1):
            result.append(f"{i}. {game['name']} - {game['playtime_forever'] // 60} uren gespeeld")
        return result
    
    def friend_list(steam_id):
        global game_count
        url = f'https://api.steampowered.com/ISteamUser/GetFriendList/v0001/'
        params = {
            'key': steam_key,
            'steamid': steam_id,
            'relationship': 'friend'
        }
        response = urequests.get(url + '?' + '&'.join([f'{k}={v}' for k, v in params.items()])).json()
        if 'friendslist' in response and 'friends' in response['friendslist']:
            friends = response['friendslist']['friends'][:5]  # Limit to max 5 friends
            friend_summaries = []
            for friend in friends:
                friend_data = player_summary(friend['steamid'])['response']['players'][0]
                personaname = friend_data['personaname']
                realname = friend_data.get('realname', '')
                loccountrycode = friend_data.get('loccountrycode', '')
                personastate = friend_data['personastate']
                if 'response' in response and 'game_count' in response['response']:
                    game_count = response['response']['game_count']
                summary_parts = [personaname]
                if realname:
                    summary_parts.append(f"({realname})")
                if loccountrycode:
                    summary_parts.append(f"({loccountrycode})")
                summary_parts.append(f"- {'Online' if personastate != 0 else 'Offline'}")
                summary_parts.append(f"- Games count: {game_count}")
                summary = ' '.join(summary_parts)
                friend_summaries.append(summary)
            return friend_summaries
        return []
    

    def online_status(steam_id):
        user_data = player_summary(steam_id)['response']['players'][0]
        return user_data['personastate'] != 0

    print(f"{play_time(steam_id)};;;{player_summary(steam_id)};;;{owned_games()};;;{top_games()};;;{friend_list(steam_id)};;;{online_status(steam_id)};;;EXIT//")

# Function to connect to WiFi
def ConnectWiFi():
    with open('network.json') as f:
        config = json.load(f)
        ssid = config[1]['ssid']
        password = config[1]['password']

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    max_wait = 50
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        status = wlan.ifconfig()
        print('ip address:', status[0])

    return wlan

# Function to set all LEDs to a specific color
def set_all_pixels(r, g, b):
    for i in range(NUM_LEDS):
        np[i] = (r, g, b)
    np.write()

# Function to get distance from HC-SR04
def get_distance():
    # Ensure Trig is low
    trig.value(0)
    time.sleep_us(2)

    # Send 10us pulse to Trig
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    # Measure Echo pulse
    duration = machine.time_pulse_us(echo, 1, 1000000)  # Timeout after 1 second
    if duration < 0:
        return None  # No echo received

    # Calculate distance in centimeters (speed of sound is ~343 m/s => 0.034 cm/us)
    distance = (duration * 0.034) / 2
    return distance

# Function to read input commands
def read_input():
    global commands
    while True:
        data = input()
        commands.append(data)

# Function to process commands
def process_commands():
    global commands
    while commands:
        command = commands.pop(0)
        if command.isdigit():
            steam_id = int(command)
            steam_api_functions(steam_id)
        elif command.startswith(';2;'):
            command = command.replace(';2;', '')
            try:
                playtime, limit = map(int, command.split(';;'))
                print(';;;2;;;')
                if playtime >= limit:
                    set_all_pixels(255, 0, 0)
            except ValueError:
                print(f"Invalid command format: {command}")
        else:
            print(f"Unknown command: {command}")

# Main loop
async def main_loop():
    while True:
        distance = get_distance()
        if distance is not None and distance < DETECTION_DISTANCE:
            set_all_pixels(0, 0, 0)
            time.sleep(DEBOUNCE_TIME)
        process_commands()
        await asyncio.sleep(0.5)

# Connect to WiFi
wifi = ConnectWiFi()

# Start the input thread
_thread.start_new_thread(read_input, ())

# Run the async event loop
loop = asyncio.get_event_loop()
loop.create_task(main_loop())
loop.run_forever()


