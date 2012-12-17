from spreadsheet import Spreadsheet 
from oled import Oled
from rgbled import RgbLed
from encoder import Encoder

encoder = Encoder()
encoder.start_monitor()
oled = Oled()
ss = Spreadsheet()
rgbled = RgbLed()
rgbled.set(0,0,2)

worksheet = ss.worksheet(1)
projects = worksheet.get_list()
for project in projects:
    print project

rgbled.fade(0,0,100)
oled.display(projects[0]['name'])

contrast = 0
contrast_changed = False
idle = 0
while True:
    delta = encoder.get_delta()
    switch = encoder.get_switch_state()
    if switch>0:
        contrast_changed = True
        idle = 0

    if delta!=0:
        idle = 0
        contrast += delta
        if contrast<=0:
            contrast = 255
        elif contrast>255:
            contrast = 0

        oled.ssd1306.set_contrast(contrast)
        p = int(contrast*100.0/255.0)
        rgbled.set(p,0,100-p)
        contrast_changed = True
    else:
        if contrast_changed:
            contrast_changed = False
            oled.display("%d" % contrast)
        idle += 1
        if idle == 5000:
            oled.display(projects[0]['name'])
