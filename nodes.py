import globals
import gui
import sllcp
import threading

from tkinter import *
from tkinter import ttk

from time import sleep

import serial_packet_sender as sps

node_window = None
len_select = None
right_txt = None

node_len = None
echo_opt = None

serial_node = None

capabilities = bytearray()


class SllcpNode:
    def __init__(self, man, mod, dmx, wif, eth, dev, idi, ido, imi, imo, ilo, iso):
        self.manufacturer = man
        self.model_name = mod
        self.dmx_length = dmx
        self.has_wifi = wif
        self.has_eth = eth
        self.device = dev
        self.if_dmx_in = idi
        self.if_dmx_out = ido
        self.if_midi_in = imi
        self.if_midi_out = imo
        self.if_laser_out = ilo
        self.if_strip_out = iso

    def print_to(self, widget):
        widget.insert(END, "Device:")
        widget.insert(END, "\t%s" % self.manufacturer)
        widget.insert(END, " - %s" % self.model_name)
        widget.insert(END, "\nMode:\t%s\n" % self.dmx_length)
        widget.insert(END, "WiFi:\t%s\n" % self.has_wifi)
        widget.insert(END, "Eth:\t%s\n" % self.has_eth)
        widget.insert(END, "Type:\t%s\n" % self.device)
        widget.insert(END, "Interfaces:\n")
        widget.insert(END, " - DMX:\tinput %d / output %d\n" % (self.if_dmx_in, self.if_dmx_out))
        widget.insert(END, " - MIDI:\tinput %d / output %d\n" % (self.if_midi_in, self.if_midi_out))
        widget.insert(END, " - ILDA:\toutput %d\n" % self.if_laser_out)
        widget.insert(END, " - LED strip:\toutput %d\n" % self.if_strip_out)


def set_len():
    sps.send_setter_serial(node_len.get())


def send_opt():
    global echo_opt
    if echo_opt.get():
        sps.send_request_serial(sllcp.OpCodes.SllcpOpOptInEcho)
    else:
        sps.send_request_serial(sllcp.OpCodes.SllcpOpOptOutEcho)


def send_restart():
    sps.send_request_serial(sllcp.OpCodes.SllcpOpRestart)


def on_closing():
    print("Closing node window.")
    node_window.destroy()


def print_capabs():
    right_txt.delete('1.0', END)
    sleep(2)
    right_txt.insert(END, "Capabilities:\n")
    global capabilities
    for item in capabilities:
        right_txt.insert(END, " - %s\n" % sllcp.enum_opcodes[item])


def open_node():
    if sps.ser.isOpen():
        print("Opening node window.")
        sps.send_request_serial(sllcp.OpCodes.SllcpOpReqCapab)
        open_node_window()
        t = threading.Thread(target=print_capabs)
        t.start()

    else:
        print("There is no connected node.")


def open_node_window():
    global node_window
    node_window = Toplevel(gui.main_window)
    node_window.title("SerialNode")
    node_window.geometry("700x400")
    node_window.protocol("WM_DELETE_WINDOW", on_closing)

    container = PanedWindow(node_window, orient=VERTICAL, borderwidth=5)
    container.pack()

    # 1st strip: Collected datas
    box_label = Label(container, height=2, text="Node description:")
    container.add(box_label)

    box_strip = PanedWindow(container)
    box_strip.pack()

    left_txt = Text(box_strip, width=40, height=16, background="#304770", fg="#f0f0f0")
    box_strip.add(left_txt)

    global serial_node, right_txt
    if not serial_node is None:
        serial_node.print_to(left_txt)

    right_txt = Text(box_strip, width=40, height=16, background="#304770", fg="#f0f0f0")
    box_strip.add(right_txt)

    container.add(box_strip)
    container.add(ttk.Separator(container))

    bottom_panel = PanedWindow(container)
    bottom_panel.pack()

    left_panel = PanedWindow(bottom_panel, orient=VERTICAL, borderwidth=2, relief="groove")
    left_panel.pack()

    mode_label = Label(left_panel, height=2, text="Protocol setup:")
    left_panel.add(mode_label)

    mode_strip = PanedWindow(left_panel)
    mode_strip.pack()

    len_lbl = Label(mode_strip, text="Data packet length:")
    mode_strip.add(len_lbl)

    global len_select, node_len
    node_len = StringVar()
    node_len.set(globals.available_lengths[1])
    len_select = OptionMenu(mode_strip, node_len, *globals.available_lengths)
    mode_strip.add(len_select)

    set_leb_btn = Button(mode_strip, command=set_len, text="Set", width=14)
    mode_strip.add(set_leb_btn)

    left_panel.add(mode_strip)
    bottom_panel.add(left_panel)

    right_panel = PanedWindow(bottom_panel, orient=VERTICAL, borderwidth=2, relief="groove")
    right_panel.pack()

    admin_label = Label(right_panel, height=2, text="Administration:")
    right_panel.add(admin_label)

    admin_echo_strip = PanedWindow(right_panel)
    admin_echo_strip.pack()

    global echo_opt
    echo_opt = IntVar()
    echo_check = Checkbutton(admin_echo_strip, variable=echo_opt, command=send_opt, text="Opt-in echo messages")
    admin_echo_strip.add(echo_check)

    rst_btn = Button(admin_echo_strip, command=send_restart, text="Restart")
    admin_echo_strip.add(rst_btn)

    right_panel.add(admin_echo_strip)

    bottom_panel.add(right_panel)

    container.add(bottom_panel)
