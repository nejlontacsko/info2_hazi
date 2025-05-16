import globals
import serial
import serial_receiver as sr
import sllcp

from time import sleep

ser = serial.Serial()
receiver = None


def init_serial():
    global ser
    # ser.baudrate = 76800
    ser.baudrate = 250000
    ser.port = globals.active_port.get()
    ser.timeout = 1
    if ser.port == "COM?":
        print("Please choose COM port first.")
    else:
        ser.open()

    if ser.isOpen():
        print('Open: ' + ser.portstr)
        print(ser)
        global receiver
        receiver = sr.SerialReceiver()


def send_request_serial(oc):
    if ser.isOpen():
        packet = sllcp.simple_packet(oc)
        ser.write(packet)
    else:
        print("Couldn't send request, because the port is CLOSED.")


def send_setter_serial(mode):
    if ser.isOpen():
        packet = sllcp.set_mode_packet(sllcp.len_to_opcode(mode))
        ser.write(packet)
    else:
        print("Couldn't send setter, because the port is CLOSED.")


def multiline_serial(packet):
    for x in range(int(len(packet) / 16) + 1):
        buffer = bytearray(16)
        buffer[0:16] = packet[x * 16: (x + 1) * 16]
        # buffer.extend(b'\r\n')
        ser.write(buffer)
        ser.flush()


def send_pollreply_serial():
    packet = sllcp.pollreply_packet()
    ser.write(packet)


def send_capab_serial():
    packet = sllcp.capability_packet()
    ser.write(packet)


def send_datas_serial(length, intf, dmx_data):
    packet = sllcp.dmx_packet(sllcp.len_to_opcode(length), intf, dmx_data)
    multiline_serial(packet)


def close_serial():
    if ser.isOpen():
        send_request_serial(sllcp.OpCodes.SllcpOpDisconn)
        sleep(.1)
        ser.cancel_read()
        global receiver
        receiver.stop()
        ser.flush()
        ser.close()
        print("Serial port is closed.")
