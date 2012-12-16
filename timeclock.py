from spreadsheet import Spreadsheet 
from oled import Oled
from rgbled import RgbLed

oled = Oled()
ss = Spreadsheet()
rgbled = RgbLed()
rgbled.set(0,0,0)
rgbled.fade(0,0,100)

worksheet = ss.worksheet(1)
projects = worksheet.get_list()
for project in projects:
    print project

oled.display(projects[0]['name'])

