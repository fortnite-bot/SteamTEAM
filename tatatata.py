from machine import Pin
import utime

led = Pin(20, machine.Pin.OUT)

while True:
    #1
    led.toggle()  
    utime.sleep(0.3)  
    led.toggle()
    #2
    utime.sleep(0.3)
    led.toggle()  
    utime.sleep(0.3)
    led.toggle()  
    #3
    utime.sleep(0.3)
    led.toggle()  
    utime.sleep(0.3)
    led.toggle()
    #4
    utime.sleep(0.3)
    led.toggle()
    print('test')
    utime.sleep(2)
    led.toggle()  
