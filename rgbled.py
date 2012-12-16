import gaugette.rgbled

class RgbLed:

    PIN_R = 6
    PIN_G = 5
    PIN_B = 4
    
    def __init__(self):
        self.led = gaugette.rgbled.RgbLed(self.PIN_R, self.PIN_G, self.PIN_B)

    def set(self, r,g,b):
        self.led.set(r,g,b)

    # Revisit - use a background thread for fades        
    def fade(self, r,g,b, delay=2000):
        self.led.fade(r,g,b,delay)
