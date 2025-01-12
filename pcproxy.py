def send(message):
    from serial.tools import list_ports
    import serial
    import os

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

    with serial.Serial(port=pico_port, baudrate=115200, bytesize=8, parity='N', stopbits=1, timeout=1) as serial_port:
        if serial_port.isOpen():
            print("[INFO] Using serial port", serial_port.name)
        else:
            print("[INFO] Opening serial port", serial_port.name, "...")
            serial_port.open()

        try:
            # Request user input
            #input("Press Enter to start communication with Pico...")
            data = f"{message}\r"#get steam response
            full_output = ''
            serial_port.write(data.encode())
            while True:
                    # Turn led on by sending a '1'
                    pico_output = read_serial(serial_port)
                    pico_output = pico_output.replace('\r\n', ' ')
                    if pico_output != '\n' and pico_output != '':
                        if '[reset]' in pico_output:
                            print(pico_output)
                        elif f'{message}' in pico_output:
                            pass
                        elif "{" in pico_output or "}" in pico_output:
                            full_output += pico_output
                            if "}}" in pico_output:
                                return full_output
                        else:
                            print(pico_output)
                            
                        


        except KeyboardInterrupt:
            print("[INFO] Ctrl+C detected. Terminating.")
        finally:
            # Close connection to Pico
            print(pico_output)
            serial_port.close()
            print("[INFO] Serial port closed. Bye.")
