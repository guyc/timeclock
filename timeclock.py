from spreadsheet import Spreadsheet 
from oled import Oled
from gaugette.rgbled import RgbLed
from gaugette.rotary_encoder import RotaryEncoder
from gaugette.switch import Switch
import wiringpi
import time
import datetime
import gdata.service # for exception handling

gpio = wiringpi.GPIO(wiringpi.GPIO.WPI_MODE_PINS)

RGB_PIN_R = 6
RGB_PIN_G = 5
RGB_PIN_B = 4

startup_sequence      = [[50,0,0,500],[50,50,0,500],[0,50,0,500],[0,50,50,500],[0,0,50,500],[50,0,50,500]]
boot_sequence         = [[100,100,100]]
active_sequence       = [[0,0,50,2000],1000,[0,0,5,2000],600]  
going_active_sequence = [[0,0,50,0],[0,0,1,200],[0,0,50,200]]
idle_sequence         = [[1,0,1]]
going_idle_sequence   = [[50,0,50,0],[1,0,1,200],[50,0,50,200]]

rgbled = RgbLed.Worker(RGB_PIN_R, RGB_PIN_G, RGB_PIN_B)
rgbled.set_sequence(boot_sequence)
rgbled.start()

ENCODER_PIN_A  = 7
ENCODER_PIN_B  = 8
encoder = RotaryEncoder.Worker(ENCODER_PIN_A, ENCODER_PIN_B)
encoder.start()

SWITCH_PIN = 9
switch = Switch(SWITCH_PIN)
switch_state = switch.get_state()

oled = Oled()
contrast = 0
oled.ssd1306.set_contrast(contrast)

rgbled.set_sequence(startup_sequence)

SPREADSHEET_NAME     = 'TimeClock'
SPREADSHEET_TEMPLATE = 'TimeClock.ods'
ss = Spreadsheet()

if not ss.oauth.has_token():
    user_code = ss.oauth.get_user_code()
    print "Go to %s and enter the code %s" % (ss.oauth.verification_url, user_code)
    # need a font that will show us the full code without scrolling
    from gaugette.fonts import arial_24
    oled.ssd1306.clear_display()
    oled.ssd1306.draw_text3(0,0,user_code,arial_24)
    oled.ssd1306.display()
    ss.oauth.get_new_token()  # this call will block until the code is entered

if not ss.get_spreadsheet_by_name(SPREADSHEET_NAME):
    print "Creating new spreadsheet '%s'." % (SPREADSHEET_NAME)
    ss.create(SPREADSHEET_TEMPLATE, SPREADSHEET_NAME)

time_worksheet = ss.worksheet(0)
project_worksheet = ss.worksheet(1)
projects = project_worksheet.get_rows()
project_names = []
for project in projects:
    name = project.get_attribute('name', None)
    if name:
        color = project.get_attribute('colour')
        hide = project.get_attribute('hide')

        if hide and len(hide) and hide.lower()[0]=='y':
            print "'%s' is hidden" % (name)
        else:
            project_names.append(project['name'])
    
oled.set_list(project_names)
    
last_row = time_worksheet.get_last_row()
last_project_index = None

if last_row and not last_row['finish']:
    # we have unfinished work!
    last_project = last_row['project']
    try:
        last_project_index = project_names.index(last_project)
        # Should select this project as the active one
        oled.list.scroll(last_project_index*oled.list.rows)
    except ValueError:
        # project is not in list!
        last_row = None
else:
    last_row = None

if last_row:
    rgbled.set_sequence(active_sequence)
else:
    rgbled.set_sequence(idle_sequence)

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
        selected = oled.list.align()

        if not switch_state:
            selected = oled.list.align()
            now = time_worksheet.gdate(datetime.datetime.utcnow())
            
            ended_row = False
            # If there is an open record end it
            if last_row:
                rgbled.set_sequence(going_idle_sequence)
                last_row['finish'] = now
                # Note this uses the obscure RC relative cell syntax which is automatically converted to normal spreadsheet notation
                last_row['minutes'] = '=(R[0]C[-1]-R[0]C[-2])*60*24';
                last_row.update_or_append() # failover to append if update is blocked by Conflict error
                last_row = None
            else:
                last_project_index = None
                
            # if either there was open row, or a new project is selected
            if selected != last_project_index:
                rgbled.set_sequence(going_active_sequence)
                last_row = time_worksheet.Row(time_worksheet)
                last_row['project'] = project_names[selected]
                last_row['start'] = now
                last_row.append()
                last_project_index = selected
                
            if last_row:
                rgbled.set_sequence(active_sequence)
            else:
                rgbled.set_sequence(idle_sequence)
                
            idle = True




