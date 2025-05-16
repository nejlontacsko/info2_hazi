import sllcp
import threading

import serial_packet_sender as sps

# Start watcher on an another thread
class SerialReceiver(threading.Thread):
    def __init__(self):
        print("Receiver is starting...")
        threading.Thread.__init__(self)
        self.able_to_run = True
        self.setDaemon(True)
        self.start()

    def run(self):
        recv = "Waiting for data..."
        print(recv)
        while sps.ser.isOpen() and self.able_to_run:
            recv = sps.ser.readline()
            if len(recv) > 0:
                incoming = str(recv)
                if incoming[2 : 7] == "SLLCP":
                    sllcp.answer_received(recv)

                    print(incoming, flush=True)
                else:
                    print('Received:')
                    print(incoming, flush=True)



        print("Port is closed, receiver closes.")

    def stop(self):
        self.able_to_run = False
