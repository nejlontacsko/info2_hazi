import csv
import gui
import globals

from threading import Timer

data = None
cue = 2


class PlayerTimer(object):
    def __init__(self, function, *args, **kwargs):
        self._timer = None
        self.interval = 4
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False

    def _run(self):
        self.is_running = False
        self.daemon = True
        self._start()
        global data, cue
        # print("CueList > Cue#%d" % cue)
        if cue < data[0][0]:
            for i in range(data[0][2]):
                globals.dmxData[int(data[1][i])] = data[cue][i]
            self.function(*self.args, **self.kwargs)
            cue += 1
        else:
            self.stop()

    def _start(self):
        if not self.is_running:
                self._timer = Timer(self.interval, self._run)
                self._timer.start()
                self.is_running = True

    def start(self, interval):
        if not self.is_running:
            print("Start Player timer...")
            self.interval = interval
            print("Interval sat to %.3f ms." % self.interval)
            self._start()
        if self.is_running:
            print("Player timer is running.")

    def stop(self):
        if self.is_running:
            print("Stop Player timer...")
            self._timer.cancel()
            self.is_running = False
            global cue
            cue = 2
            print("Player timer is stopped.")



def load():
    global data
    # with open('G:\electro\SllcpPyUsb\example_cuelist.csv', newline='') as csvfile:
    with open(globals.file_path.get(), newline='') as csvfile:
        data = list(csv.reader(csvfile, delimiter=';'))

    for i in range(len(data)):
        if i != 1:
            for j in range(len(data[i])):
                data[i][j] = int(data[i][j])

    print("Loaded Cuelist:")
    print(" - Count of frames: %d" % data[0][0])
    print(" - Frame time: %d ms" % data[0][1])
    print(" - Count of affected channels: %d" % data[0][2])
    print(" - Affected channels: %s" % ", ".join(data[1]))

def play():
    global data
    timer = PlayerTimer(gui.send_dmx_data)
    timer.start(data[0][1] / 1000)