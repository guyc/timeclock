import gaugette.rotary_encoder
import gaugette.switch
import threading
import time

class Encoder:

    class Monitor(threading.Thread):
        def run(self):
            while True:
                self.encoder.delta += self.encoder.encoder.get_delta()
                time.sleep(0.001)
            
    A_PIN  = 7
    B_PIN  = 9
    SW_PIN = 8
    def __init__(self):
        self.encoder = gaugette.rotary_encoder.RotaryEncoder(self.A_PIN, self.B_PIN)
        self.switch = gaugette.switch.Switch(self.SW_PIN)
        self.delta = 0

    def start_monitor(self):
        self.monitor = self.Monitor()
        self.monitor.encoder = self
        self.monitor.start()

    def get_switch_state(self):
        return self.switch.get_state()

    def get_delta(self):
        # revisit - should be atomic or locking
        delta = self.delta
        self.delta -= delta
        return delta
