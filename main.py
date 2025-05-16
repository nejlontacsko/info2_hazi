from datetime import datetime
from tkinter import *

import argparse
import globals
import gui
import math
import signal
import sllcp
import sys
import threading

import zh_kerdes

import serial_packet_sender as sps
import polling_timer as tim

from time import sleep


# An easier (and more transparent) way to give feedback for the user.
class StdoutRedirect(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag
        self.tim = False

    def write(self, msg):
        self.widget.config(state="normal")
        if self.tim and len(msg) > 1:
            self.widget.insert(END, "[%s] " % (datetime.now().strftime("%H:%M:%S")))
        self.widget.insert(END, msg)
        self.widget.see(END)
        self.widget.config(state="disabled")

    def flush(self):
        pass

    def enable_timestamp(self):
        self.tim = True


def goodbye():
    sps.close_serial()
    print("Goodbye.")
    sys.exit(0)


def signal_handler():
    print('KeyboardInterrupt received. Shutting down...')
    globals.polling_timer.stop()
    goodbye()


# -------BEGIN------- #
# LEGACY CODE FROM CONSOLE LINE ERA
# Prepare for healthy shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGBREAK, signal_handler)

# Setup commandline helper and switches
parser = argparse.ArgumentParser(description="SLLCP server simulation on Serial Port")
parser.add_argument('-p', '--port', action='store', help='SerialPort name')
parser.add_argument('-t', '--timeout', type=int, action='store', help='Stop server after TIMEOUT secs.')
parser.add_argument('-d', '--dmxlength', type=int, action='store',
                    help='Sets the DMX length.\nOnly 256, 512, 1024 or 2048 accepted.')
args = parser.parse_args()

if args.dmxlength not in [256, 512, 1024, 2048]:
    globals.dmx_length = globals.available_lengths[1]
    print("Invalid DMX length given. Length sat to 512 automatically.")
else:
    globals.dmx_length = globals.available_lengths[int(math.log2(args.dmxlength >> 7))]

# TODO: convert length to opcode, make a setter into sllcp module
# END OF LEGACY CODE


globals.polling_timer = tim.PollingTimer(sps.send_request_serial, sllcp.OpCodes.SllcpOpPoll)
gui.init_gui()


# Wait a moment while the From builds up...
while gui.txt is None:
    pass

zh_kerdes.kerdes()

sys.stdout = StdoutRedirect(gui.txt, "stdout")
print("          Stage Lighting and Laser Control Protocol          ")
print("-------------------------------------------------------------")
sys.stdout.enable_timestamp()
print("Ready.")

gui.main_window.mainloop()

# --------END-------- #
