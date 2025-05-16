from tkinter import *

from datetime import datetime

color = (0, 0, 0)

available_lengths = [
    "DMX-256",
    "DMX-512",
    "DMX-1024",
    "DMX-2048"
]

dmx_length = None
active_port = None
file_path = None

polling_timer = None

serial_node = None

dmxData = bytearray(2048)

last_seen = datetime.now()


def init_tk_globals():
    global dmx_length
    dmx_length = StringVar()
    dmx_length.set(available_lengths[1])

    global active_port
    active_port = StringVar()
    active_port.set("COM?")

    global file_path
    file_path = StringVar()
