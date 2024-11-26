from machine import Pin
import time

led_pin = Pin(20, Pin.OUT)
red_switch_pin = Pin(19, Pin.IN, pull=Pin.PULL_DOWN)
green_switch_pin = Pin(16, Pin.IN, pull=Pin.PULL_DOWN)

while True:
    if green_switch_pin.value():
        led_pin.on()
    else:
        led_pin.off()
    time.sleep(0.1)
    
