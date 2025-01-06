import machine
import time
import neopixel
import network
from time import sleep
import urequests
import time

ssid = ''
password = ''
#remove all prints other than api response

def make_request(url):
    try:
        response = urequests.get(url)        
        # Print first few lines of response content
        print("\nFirst few lines of response:")
        print(response.text[:200])
        
    except Exception as e:
        print(f"Error occurred: {e}")


def ConnectWiFi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        sleep(1)
    
    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connecteda')
        status = wlan.ifconfig()
        print('ip address:', status[0])
# URL to request
        url = "http://www.example.com"

        # Make the request
        make_request(url)

        # Wait a bit before exiting
        time.sleep(5)

    return wlan

wifi = ConnectWiFi()

# === Configuration ===

# HC-SR04 Pins
TRIG_PIN = 17     # GPIO5
ECHO_PIN = 16    # GPIO18

# WS2812 LED Setup
NUM_LEDS = 8         # Number of LEDs in the strip
LED_PIN = 18          # GPIO4 (commonly used for NeoPixels)

# Detection Parameters
DETECTION_DISTANCE = 10    # Distance in centimeters to trigger the LEDs
DEBOUNCE_TIME = 0        # Seconds to wait before re-detecting

# === Initialize Hardware ===

# Initialize Trig and Echo pins
trig = machine.Pin(TRIG_PIN, machine.Pin.OUT)
echo = machine.Pin(ECHO_PIN, machine.Pin.IN)

# Initialize NeoPixel
np = neopixel.NeoPixel(machine.Pin(LED_PIN), NUM_LEDS)

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

# === Main Loop ===
try:
    while True:
        distance = get_distance()
        if distance is not None:
            print("Distance:", distance, "cm")
            if distance < DETECTION_DISTANCE:
                # Turn all LEDs to red
                set_all_pixels(255, 0, 0)
                # Wait for debounce_time before next detection
                time.sleep(DEBOUNCE_TIME)
            else:
                # Turn off LEDs if not within detection range
                set_all_pixels(0, 0, 0)
        else:
            print("No echo received or out of range")
            # Optionally, turn off LEDs if no valid echo
            set_all_pixels(0, 0, 0)

        # Short delay to prevent excessive looping
        time.sleep(0.5)

except KeyboardInterrupt:
    # Gracefully handle a keyboard interrupt (Ctrl+C)
    set_all_pixels(0, 0, 0)
    print("Program stopped")

