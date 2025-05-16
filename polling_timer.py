from threading import Timer

from datetime import datetime
import globals


class PollingTimer(object):
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
        self.function(*self.args, **self.kwargs)
        if datetime.now().timestamp() - globals.last_seen > 10:
            globals.serial_node.config(background="#ffff00")

    def _start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def start(self, interval):
        if not self.is_running:
            print("Start Polling timer...")
            self.interval = interval
            print("Interval sat to %d secs." % self.interval)
            self._start()
        if self.is_running:
            print("Polling timer is running.")

    def stop(self):
        if self.is_running:
            print("Stop Polling timer...")
            self._timer.cancel()
            self.is_running = False
            print("Polling timer is stopped.")
