"""
n = need to know
c = can do

s = send
r = receive
"""
from datetime import datetime

import globals
import nodes
import serial_packet_sender as sps


class OpCodes:
    SllcpOpTestMsg = 0x00
    SllcpOpRestart = 0x01      # cs
    # SllcpOpShutdown = 0x02
    SllcpOpDisconn = 0x03      # cs
    SllcpOpPoll = 0x10         # cs
    SllcpOpPollReply = 0x11    # csr
    # SllcpOpPollResults = 0x12
    # SllcpOpOutLaser = 0x21
    # SllcpOpOutClose = 0x20
    # SllcpOpOutStrip = 0x22
    SllcpOpOutAck = 0x2f
    # SllcpOpGetIpConf = 0x30
    # SllcpOpGetApList = 0x31
    SllcpOpSetMode = 0x40      # csr
    # SllcpOpSetIpAdd = 0x41
    # SllcpOpSetWiFiAP = 0x42
    SllcpOpSetAck = 0x4f
    # SllcpOpAPReply = 0x52
    SllcpOpOutDMX256 = 0xc0    # cs
    SllcpOpOutDMX512 = 0xd0    # cs
    SllcpOpOutDMX1k = 0xe0     # cs
    SllcpOpOutDMX2k = 0xf0     # cs

    # ******************* #
    # * Brand NEW stuff * #
    # ******************* #

    # Requests the receiver to return or not return the following packages.
    SllcpOpOptInEcho = 0x04    # cs
    SllcpOpOptOutEcho = 0x05   # cs

    # Request for PollResults
    # SllcpOpReqPollRes = 0x13

    # Request for Capabilities
    SllcpOpReqCapab = 0x14     # csr

    # Answer for ReqCapab with a list of the available OpCodes and the used protocol version
    #  and let's make the system chinese-proof: if the node doesn't answer, the server should
    #  mark the Node with UNRELIABLE tag.
    SllcpOpCapability = 0x15   # csr

    # RDM encapsulation
    # SllcpOpRDM = 0xa0

    # DMX packet compressed with Run-length encoding for low-end hardware. Bits [3..0] are interface selectors.
    SllcpOpOutDMXcRLE = 0xb0   # If i'll have some free time


class DevCodes:
    DevController = 0,
    DevServer = 1,
    DevNode = 2,
    DevVisualizer = 3


version = 0x14

enum_opcodes = {value: name for name, value in vars(OpCodes).items()}
enum_devices = {value: name for name, value in vars(DevCodes).items()}

header = b'SLLCPv'
packet = bytearray()

fwdIp = bytearray([192, 168, 0, 1])  # IP routing is opted-out in this project.
dmxLn = 0xd0  # (d0 -> 512) TODO: make a cmd line switch for this


def filling_generator(amount):
    arr = bytearray()
    for x in range(amount):
        arr.append(0xaa + (x % 6 * 0x11))
    return arr


def packet_reset(v):
    global packet
    packet = bytearray(header)
    packet.append(v)
    packet.append(0x00)


def get_seq_id():
    get_seq_id.seqId += 1
    return get_seq_id.seqId.to_bytes(4, byteorder="big")


get_seq_id.seqId = int(0)  # Really weird `static` solution, but if it works... But the seqId MUST BE protected!


def len_to_opcode(s):
    switcher = {
        "DMX-256": OpCodes.SllcpOpOutDMX256,
        "DMX-512": OpCodes.SllcpOpOutDMX512,
        "DMX-1024": OpCodes.SllcpOpOutDMX1k,
        "DMX-2048": OpCodes.SllcpOpOutDMX2k,
        "256": OpCodes.SllcpOpOutDMX256,
        "512": OpCodes.SllcpOpOutDMX512,
        "1024": OpCodes.SllcpOpOutDMX1k,
        "2048": OpCodes.SllcpOpOutDMX2k
    }
    return switcher.get(str(s), 0)


def simple_packet(op_code):
    def switch(oc):
        switcher = {
            OpCodes.SllcpOpPoll: "Polling request.",
            OpCodes.SllcpOpRestart: "Request for software restart.",
            OpCodes.SllcpOpDisconn: "Annunciation of leaving.",
            OpCodes.SllcpOpReqCapab: "Capability request.",
            OpCodes.SllcpOpOptInEcho: "OPT-IN ECHO",
            OpCodes.SllcpOpOptOutEcho: "OPT-OUT ECHO"
        }
        return switcher.get(oc, "Invalid packet!")

    print("[Op:0x{:02x}] Sending {}".format(op_code, switch(op_code)))

    global packet
    if op_code == OpCodes.SllcpOpReqCapab:
        packet_reset(0x14)
    else:
        packet_reset(0x00)
    packet.append(op_code)
    packet.extend(b'\r\n')
    return packet


def set_mode_packet(mode_code):
    op_code = OpCodes.SllcpOpSetMode

    print("[Op:0x{:02x}] Sending mode setter.".format(op_code))

    global packet
    packet_reset(0x12)
    packet.append(op_code)
    packet.append(mode_code)
    packet.extend(b'\r\n')
    return packet


def dmx_length_switch(oc):
    switcher = {
        OpCodes.SllcpOpOutDMX256: "DMX-256",
        OpCodes.SllcpOpOutDMX512: "DMX-512",
        OpCodes.SllcpOpOutDMX1k: "DMX-1024",
        OpCodes.SllcpOpOutDMX2k: "DMX-2048"
    }
    return switcher.get(oc, "Invalid packet! (%x)" % oc)


def dmx_packet(length: int, intf, dmx_data):
    if intf > 15 or intf < 0:
        raise ValueError("Interface ID must be in range of [0..15].")

    global packet
    # op = dmxLn | (((dmxLn - 0xc0) & 0x30) >> 2) | intf
    op = length | intf
    print("[Op:0x{:02x}] Sending {} format lighting data.".format(op, dmx_length_switch(length)))
    packet_reset(0x10)
    packet.append(op)
    packet.extend(filling_generator(3))
    packet.extend(get_seq_id())
    packet.extend(fwdIp)
    packet.extend(dmx_data)
    packet.extend(b'\r\n')
    return packet


def pollreply_packet():
    op_code = OpCodes.SllcpOpPollReply

    print("[Op:0x{:02x}] Sending reply for the poll request.".format(op_code))

    global packet
    packet_reset(0x10)
    packet.append(op_code)

    packet.extend(bytes("Nejlontacsko".ljust(15, '\0'), encoding='ascii'))
    packet.extend(bytes("Python jammer".ljust(16, '\0'), encoding='ascii'))

    packet.append(0xcf | len_to_opcode(globals.dmx_length.get()) & 0x30)
    packet.extend([0, 0, 1])
    packet.extend(b'\r\n')

    return packet


def capability_packet():
    op_code = OpCodes.SllcpOpCapability

    print("[Op:0x{:02x}] Sending mode setter.".format(op_code))

    global packet, version
    packet_reset(version)
    packet.append(op_code)
    list_of_opcodes = []
    for item in vars(OpCodes).values():
        if type(item) is int:
            list_of_opcodes.append(item)
    list_of_opcodes.sort()
    packet.extend(list_of_opcodes)
    packet.extend(b'\r\n')
    return packet


def answer_received(incoming):
    oc = incoming[8]
    print("[Op:0x%02x] %s received." % (incoming[8], enum_opcodes[incoming[8]]))

    if oc == OpCodes.SllcpOpTestMsg:
        print(incoming, flush=True)
    elif oc == OpCodes.SllcpOpDisconn:
        globals.serial_node.config(background="#ff0000")
    elif oc == OpCodes.SllcpOpPoll:
        sps.send_pollreply_serial()
    elif oc == OpCodes.SllcpOpPollReply:
        globals.serial_node.config(state="normal")
        manufacture = bytearray(15)
        model_name = bytearray(16)

        for i in range(15):
            c = incoming[9 + i]
            if c > 0:
                manufacture[i] = c
        for i in range(15):
            c = incoming[24 + i]
            if c > 0:
                model_name[i] = c

        nodes.serial_node = nodes.SllcpNode(
            manufacture.decode(),
            model_name.decode(),
            dmx_length_switch(0xc0 | incoming[40] & 0x30),
            incoming[40] & 0x08 > 0,
            incoming[40] & 0x04 > 0,
            enum_devices[incoming[40] & 0x03],
            (incoming[41] & 0xf0) >> 4,
            incoming[41] & 0x0f,
            (incoming[42] & 0xf0) >> 4,
            incoming[42] & 0x0f,
            (incoming[43] & 0xf0) >> 4,
            incoming[43] & 0x0f
        )
        if nodes.serial_node.model_name == "SerialNode":
            globals.serial_node.config(background="#00ff00")
            globals.last_seen = datetime.now().timestamp()
    elif oc == OpCodes.SllcpOpSetMode:
        length = dmx_length_switch(incoming[9])
        globals.dmx_length.set(length)
        print('Setting length to: %s' % length)
    elif oc == OpCodes.SllcpOpReqCapab:
        sps.send_capab_serial()
    elif oc == OpCodes.SllcpOpCapability:
        nodes.capabilities.clear()
        for i in range(9, len(incoming) - 2):
            nodes.capabilities.append(incoming[i])
    else:
        print("Ignoring packet.")
