from spreadsheet import Spreadsheet 
from oled import Oled
from gaugette.rgbled import RgbLed
from gaugette.rotary_encoder import RotaryEncoder
from gaugette.switch import Switch
import wiringpi
import time
import datetime
import utc

gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)

RGB_PIN_R = 6
RGB_PIN_G = 5
RGB_PIN_B = 4
rgbled = RgbLed.Worker(RGB_PIN_R, RGB_PIN_G, RGB_PIN_B)
rgbled.set_sequence([[0,0,2]])
rgbled.start()

ENCODER_PIN_A  = 7
ENCODER_PIN_B  = 9
encoder = RotaryEncoder.Worker(ENCODER_PIN_A, ENCODER_PIN_B)
encoder.start()

SWITCH_PIN = 8
switch = Switch(SWITCH_PIN)
switch_state = switch.get_state()

oled = Oled()
contrast = 0
oled.ssd1306.set_contrast(contrast)

rgbled.set_sequence([[2,0,2]])

ss = Spreadsheet()

time_worksheet = ss.worksheet(0)
project_worksheet = ss.worksheet(1)
projects = project_worksheet.get_rows()
project_names = []
for project in projects:
    project_names.append(project['name'])
print projects

oled.set_list(project_names)
    
last_row = time_worksheet.get_last_row()
last_project_index = None

if not last_row['finish']:
    # we have unfinished work!
    last_project = last_row['project']
    try:
        last_project_index = project_names.index(last_project)
        print [last_project, last_project_index]
        # Should select this project as the active one
        print "scrolling ",last_project_index*oled.list.rows
        oled.list.scroll(last_project_index*oled.list.rows)
    except ValueError:
        # project is not in list!
        print [last_project, project_names]
        last_row = None
else:
    last_row = None
        
if False:
    list_feed = time_worksheet.get_list_feed()
    last_entry = list_feed.entry[-1]
    row = time_worksheet.Row(time_worksheet, last_entry)
    print row['finish']
    row['finish'] += 'ya'
    print row['finish']
    row.update()
    #//row = timelog.get_last_row()
    #//row['finish'] = 'Booyeah'
    #//gd_client = ss.get_gd_client()
    #//gd_client.UpdateRow(last_entry, row)

rgbled.set_sequence([[0,0,50,2000],1000,[0,0,5,2000],600])

idle = 0
idle_counter = 0
idle = True

while True:
    time.sleep(0.01)
    delta = encoder.get_delta()

    if delta != 0:
        oled.list.scroll(delta*2)
        idle_counter = 100
        idle = False

    elif not idle:
        if idle_counter > 0:
            idle_counter -= 1
        else:
            oled.list.align()
            idle = True
    else:
        oled.list.auto_pan()

    new_switch_state = switch.get_state()
    if new_switch_state != switch_state: 
        switch_state = new_switch_state
        
        if switch_state:
            print "close"
        else:
            selected = oled.list.align()
            now = time_worksheet.gdate(datetime.datetime.utcnow())

            # If there is an open record end it
            if last_row:  
                last_row['finish'] = now
                last_row.update()
                last_row = None

            # if a new project was selected, start it
            if selected != last_project_index:
                last_row = time_worksheet.Row(time_worksheet)
                last_row['project'] = projects[selected]['name']
                last_row['start'] = now
                last_row.append()
                last_project_index = selected
                
            idle = True




