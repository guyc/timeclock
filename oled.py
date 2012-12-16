import gaugette.ssd1306
from gaugette.fonts import magneto_32

class Oled:
    RESET_PIN = 15
    DC_PIN    = 16
    CONTRAST  = 0x00   # 0 to 255, 255 is brighest
    
    def __init__(self):
        self.ssd1306 = gaugette.ssd1306.SSD1306(reset_pin=self.RESET_PIN, dc_pin=self.DC_PIN)
        self.ssd1306.begin()
        self.ssd1306.clear_display()
        self.ssd1306.flip_display()
        self.ssd1306.set_contrast(self.CONTRAST)
        self.font = magneto_32
        self.display("Gaugette")

    def display(self, text):
          self.ssd1306.clear_display()    
          self.ssd1306.draw_text3(0,0,text,self.font)
          self.ssd1306.display()

    
