from tkinter import *
from tkinter import ttk
from tkinter import colorchooser
from tkinter import messagebox
from tkinter.filedialog import askopenfilename

from functools import partial

import serial.tools.list_ports
import serial_packet_sender as sps

import globals
import nodes
import player
import sllcp

from threading import Timer
from time import sleep
from datetime import datetime

main_window = None
txt = None
com_select = None
poll_nud = None
file_path = None

r_ch_nud = None
g_ch_nud = None
b_ch_nud = None

len_select = None

sc_values = []


def channel_set(ch, va):
    print("Channel %03d: DEC %03d %03d%%, HEX %02x" % (ch, int(va), float(va) / 255 * 100, int(va)))


# Dummy event handler function for the Node selector buttons.
def asd():
    print("Button pressed.")


def send_dmx_data():
    if sps.ser.isOpen():
        switcher = {
            "DMX-256": 256,
            "DMX-512": 512,
            "DMX-1024": 1024,
            "DMX-2048": 2048
        }
        length = switcher.get(globals.dmx_length.get(), 0)

        for i in range(len(sc_values)):
            globals.dmxData[i] = sc_values[i].get()

        sps.send_datas_serial(length, 0, globals.dmxData[0:length])
    else:
        print("The Port is CLOSED, can't send DMX data packet.")


# noinspection PyUnresolvedReferences
def collect_serial():
    com_select['menu'].delete(0, END)
    print("Available COM ports: ")
    for item in serial.tools.list_ports.comports():
        print(" - %s" % item.description)
        com_select['menu'].add_command(label=item.name, command=lambda value=item.name: globals.active_port.set(value))


def color_picker():
    chosen_color = colorchooser.askcolor(title="Choose color")
    globals.color = chosen_color[0]
    print("The chosen color is:")
    print(chosen_color)


# Event handler function for the Color setter.
def set_color():
    global r_ch_nud, g_ch_nud, b_ch_nud
    globals.dmxData[int(r_ch_nud.get())] = globals.color[0]
    globals.dmxData[int(g_ch_nud.get())] = globals.color[1]
    globals.dmxData[int(b_ch_nud.get())] = globals.color[2]
    print("Color sat.")


def file_search():
    given_file_path = askopenfilename()
    print("The chosen file is:")
    print(given_file_path)
    globals.file_path.set(given_file_path)


def start_polling():
    if sps.ser.isOpen():
        globals.last_seen = datetime.now().timestamp()
        global poll_nud
        globals.polling_timer.start(int(poll_nud.get()))
    else:
        print("The Port is CLOSED, can't start polling timer.")


def on_closing():
    if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
        globals.polling_timer.stop()
        sps.close_serial()
        global main_window
        main_window.destroy()


# Create and setup the main window than fill up with form elements.
def init_gui():
    global main_window
    main_window = Tk()
    main_window.title("SLLCP serial port traffic generator")
    main_window.config(width=1100, height=700, background='#203760')
    main_window.pack_propagate(0)

    main_window.protocol("WM_DELETE_WINDOW", on_closing)

    globals.init_tk_globals()

    container = PanedWindow(main_window)
    container.pack(padx=30, pady=30, fill=BOTH)

    # LEFT panel: console
    global txt
    txt = Text(width=61, height=100, background="#304770", fg="#f0f0f0")
    txt.pack()
    container.add(txt)

    # MIDDLE panel: strips of modules
    middle_panel = PanedWindow(container, orient=VERTICAL, borderwidth=2, relief="groove")
    middle_panel.pack()
    container.add(middle_panel)

    # 1st strip: Serial select
    serial_lbl = Label(middle_panel, height=2, text="Serial Port:")
    middle_panel.add(serial_lbl)

    serial_strip = PanedWindow(middle_panel)
    serial_strip.pack()

    collect_com_btn = Button(serial_strip, command=collect_serial, text="Collect available ports")
    serial_strip.add(collect_com_btn)

    global com_select
    com_select = OptionMenu(serial_strip, variable=globals.active_port, value=["COM?"])
    serial_strip.add(com_select)

    open_com_btn = Button(serial_strip, command=sps.init_serial, text="Open serial port")
    serial_strip.add(open_com_btn)

    close_com_btn = Button(serial_strip, command=sps.close_serial, text="Close")
    serial_strip.add(close_com_btn)

    middle_panel.add(serial_strip)
    middle_panel.add(ttk.Separator(middle_panel))

    # 2nd strip: Protocol setup
    prot_lbl = Label(middle_panel, height=2, text="Protocol setup:")
    middle_panel.add(prot_lbl)

    prot_set_strip = PanedWindow(middle_panel)
    prot_set_strip.pack()

    len_lbl = Label(prot_set_strip, text="Data packet length:")
    prot_set_strip.add(len_lbl)

    global len_select
    len_select = OptionMenu(prot_set_strip, globals.dmx_length, *globals.available_lengths)
    prot_set_strip.add(len_select)

    middle_panel.add(prot_set_strip)
    prot_run_strip = PanedWindow(middle_panel)
    prot_run_strip.pack()

    poll_lbl = Label(prot_run_strip, text="Polling interval [s]:")
    prot_run_strip.add(poll_lbl)

    global poll_nud
    poll_nud = Spinbox(prot_run_strip, width=10, from_=1, to=12)
    prot_run_strip.add(poll_nud)

    timer_lbl = Label(prot_run_strip, text="Polling:")
    prot_run_strip.add(timer_lbl)

    timer_start_btn = Button(prot_run_strip, command=start_polling, text="Start Timer")
    prot_run_strip.add(timer_start_btn)

    timer_stop_btn = Button(prot_run_strip, command=globals.polling_timer.stop, text="Stop")
    prot_run_strip.add(timer_stop_btn)

    middle_panel.add(prot_run_strip)
    middle_panel.add(ttk.Separator(middle_panel))

    # 3rd strip: CueList from file
    file_lbl = Label(middle_panel, height=2, text="CueList File:")
    middle_panel.add(file_lbl)

    file_strip = PanedWindow(middle_panel)
    file_strip.pack()

    file_path_lbl = Label(file_strip, text="Path:")
    file_strip.add(file_path_lbl)

    global file_path
    file_path = Entry(file_strip, textvariable=globals.file_path, width=45)
    file_strip.add(file_path)

    file_path_btn = Button(file_strip, command=file_search, text="...")
    file_strip.add(file_path_btn)

    file_open_btn = Button(file_strip, command=player.load, text="Open")
    file_strip.add(file_open_btn)

    middle_panel.add(file_strip)
    middle_panel.add(Button(middle_panel, command=player.play, text="Play CueList"))

    middle_panel.add(ttk.Separator(middle_panel))

    # 4th strip: ColorChooser
    color_lbl = Label(middle_panel, height=2, text="RGB Channels:")
    middle_panel.add(color_lbl)

    color_channel_strip = PanedWindow(middle_panel)
    color_channel_strip.pack()

    global r_ch_nud
    r_lbl = Label(color_channel_strip, text="Red Ch:")
    color_channel_strip.add(r_lbl)
    r_ch_nud = Spinbox(color_channel_strip, width=10, from_=1, to=512)
    color_channel_strip.add(r_ch_nud)

    global g_ch_nud
    g_lbl = Label(color_channel_strip, text="Green Ch:")
    color_channel_strip.add(g_lbl)
    g_ch_nud = Spinbox(color_channel_strip, width=10, from_=1, to=512)
    color_channel_strip.add(g_ch_nud)

    global b_ch_nud
    b_lbl = Label(color_channel_strip, text="Blue Ch:")
    color_channel_strip.add(b_lbl)
    b_ch_nud = Spinbox(color_channel_strip, width=10, from_=1, to=512)
    color_channel_strip.add(b_ch_nud)

    middle_panel.add(color_channel_strip)
    color_setter_strip = PanedWindow(middle_panel)
    color_setter_strip.pack()

    color_pick_btn = Button(color_setter_strip, command=color_picker, text="Pick color")
    color_setter_strip.add(color_pick_btn)

    color_set_btn = Button(color_setter_strip, command=set_color, text="Set color")
    color_setter_strip.add(color_set_btn)

    middle_panel.add(color_setter_strip)
    middle_panel.add(ttk.Separator(middle_panel))

    # 5th strip: Faders
    fader_lbl = Label(middle_panel, height=2, text="Mixer (Ch. 1-8):")
    middle_panel.add(fader_lbl)

    fader_strip = PanedWindow(middle_panel)
    fader_strip.pack()

    global sc_values
    for i in range(8):
        sc_values.append(IntVar())

    for i in range(8):
        sc = Scale(fader_strip, command=partial(channel_set, i), from_=255, to=0)
        sc.config(variable=sc_values[i])
        fader_strip.add(sc)

    middle_panel.add(fader_strip)

    # 6th strip: Send button
    btn = Button(middle_panel, height=4, command=send_dmx_data, text="Send DMX packet!")
    middle_panel.add(btn)

    # last strip: Fill empty space
    area_fill = Label()
    middle_panel.add(area_fill)

    # RIGHT panel: available nodes
    right_panel = PanedWindow(container, orient=VERTICAL, borderwidth=2, relief="groove")
    right_panel.pack()

    node_lbl = Label(right_panel, height=2, text="Network:")
    right_panel.add(node_lbl)

    # Fill empty space
    fill_node = Label(container)
    right_panel.add(fill_node)

    globals.serial_node = Button(right_panel, height=1, command=nodes.open_node, text="SerialNode")
    globals.serial_node.config(state="disabled")
    right_panel.add(globals.serial_node, before=fill_node)

    # Every node will be added before the filler.
    for i in range(4):
        node = Button(right_panel, height=1, command=asd, text="Node %d" % i)
        node.config(state="disabled")
        right_panel.add(node, before=fill_node)

    container.add(right_panel)
