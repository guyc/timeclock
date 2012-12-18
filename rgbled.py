import gaugette.rgbled
import threading
import time

class RgbLed:

    PIN_R = 6
    PIN_G = 5
    PIN_B = 4

    class Worker(threading.Thread):
        def __init__(self, led):
            threading.Thread.__init__(self)
            self.actions = [[0,0,0,200],[0,0,50,200]]  # initial pattern
            self.condition = threading.Condition()
            self.daemon = True
            self.led = led
            self.set(0,0,0)
            self.changed = False

        def set_actions(self, actions):
            self.condition.acquire()
            self.actions = actions
            self.changed = True
            self.condition.notify()
            self.condition.release()

        def set(self, r,g,b):
            self.red = r
            self.green = g
            self.blue = b
            self.led.set(r,g,b)
            
        def run(self):
            self.condition.acquire()
            self.changed = True
            while True:
                if self.changed:
                    self.changed = False
                    actions = self.actions
                    count = len(actions)
                    i = 0
                    
                action = actions[i]
                i = (i + 1) % count
                if hasattr(action, '__iter__'):
                    if len(action)==3:
                        self.set(action[0],action[1],action[2])
                        self.condition.wait()
                    else:
                        red   = action[0]
                        green = action[1]
                        blue  = action[2]
                        delay = action[3]
                        step = 10
                        for j in range(0, delay, step):
                            f = (j+0.0) / delay
                            r = int(self.red   + (red  -self.red)   * f)
                            g = int(self.green + (green-self.green) * f)
                            b = int(self.blue  + (blue -self.blue)  * f)
                            self.led.set(r,g,b)
                            self.condition.wait(step / 1000.0)
                            if self.changed:
                                break
                        self.set(red,green,blue)
                else:
                    # must be a simple delay
                    self.condition.wait(action / 1000.0)
    
    def __init__(self):
        self.led = gaugette.rgbled.RgbLed(self.PIN_R, self.PIN_G, self.PIN_B)
        self.thread = self.Worker(self.led)
        self.thread.start()

    def set(self, r,g,b):
        self.led.set(r,g,b)

    def set_actions(self, actions):
        self.thread.set_actions(actions)
    
    # Revisit - use a background thread for fades        
    def fade(self, r,g,b, delay=2000):
        self.led.fade(r,g,b,delay)
