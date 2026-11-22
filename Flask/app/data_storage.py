from threading import Lock
import os
import threading
import time
import logging

from serial import Serial, SerialException

# sets up a logger and sets 5 seconds between polls and reconnect attempts
log = logging.getLogger(__name__)
RETRY_DELAY = 5
ARDUINO_PORT_ENV = "ARDUINO_PORT"

# this class holds the information that were collected from arduino
class DataStorage:

    def __init__(self):
        self.lock = Lock()
        self.data = {
            "temperature" : None,
            "humidity" : None
        }

    # allows for update of data inside the object
    def update(self, **kwargs):
        with self.lock:
            self.data.update(kwargs)

    # returns the object data as a dictionary
    def get(self):
        with self.lock:
            return dict(self.data)

# creating a shared instance of the class
data_store = DataStorage()

# Reads the Arduino port configured in the environment (Docker Compose passes
# it from the .env file), so no port scanning is needed inside the container.
def get_arduino_port():
    port = os.environ.get(ARDUINO_PORT_ENV, "").strip()
    if not port:
        raise RuntimeError(f"{ARDUINO_PORT_ENV} is not set")
    return port

# connecting Arduino board on the configured port
def connect():
    port = get_arduino_port()
    ser = Serial(port, 9600, timeout=1)
    time.sleep(2)
    log.info("Arduino connected on: %s", port)
    return ser

# parses line read from Arduino
def parse_reading(line):
    temperature, humidity = line.split(";")
    return float(temperature), float(humidity)

# one communication cycle
def poll_once(ser):
    ser.write(b"GET\n")
    response = ser.readline().decode('utf-8', errors='ignore').strip()
    if not response:
        return
    try:
        temperature, humidity = parse_reading(response)
    except ValueError:
        log.warning("Wrong data format: %r", response)
        return
    data_store.update(temperature=temperature, humidity=humidity)

# one cycle of communication and error handling loop
def poll_step(ser):
    try:
        if ser is None:
            ser = connect()
        poll_once(ser)
        return ser
    except (RuntimeError, SerialException, OSError) as e:
        # If Arduino has not been found or has been disconnected
        log.warning("Arduino not found: %s", e)
        data_store.update(temperature=None, humidity=None)
        if ser is not None:
            try:
                ser.close()
            except Exception:
                pass
        return None


# this function will be used by a separate thread to read data from the arduino
# wrapper function for all the above
def read_parameters():
    ser = None
    while(True):
        ser = poll_step(ser)
        time.sleep(RETRY_DELAY)

# function that sets up the thread reading data from arduino
def start_comm_thread():
    if getattr(start_comm_thread, "started", False):
        return
    start_comm_thread.started = True
    t = threading.Thread(target=read_parameters, daemon=True)
    t.start()