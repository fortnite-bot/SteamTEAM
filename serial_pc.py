from serial.tools import list_ports
import serial


def read_serial(port):
    """Read data from serial port and return as string."""
    line = port.read(1000)
    return line.decode()


# First manually select the serial port that connects to the Pico
serial_ports = list_ports.comports()

print("[INFO] Serial ports found:")
for i, port in enumerate(serial_ports):
    print(str(i) + ". " + str(port.device))

pico_port = serial_ports[0].device

# Open a connection to the Pico
with serial.Serial(port=pico_port, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=999) as serial_port:
    if serial_port.isOpen():
        print("[INFO] Using serial port", serial_port.name)
    else:
        print("[INFO] Opening serial port", serial_port.name, "...")
        serial_port.open()

    try:
        while True:
            pico_output = read_serial(serial_port)
            if pico_output:
                pico_output = pico_output.replace('\r\n', ' ')
                print("[PICO] " + pico_output) #steam api response
                break
           
    except KeyboardInterrupt:
        print("[INFO] Ctrl+C detected. Terminating.")
    finally:
        # Close connection to Pico
        serial_port.close()
        print("[INFO] Serial port closed. Bye.")
