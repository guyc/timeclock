#!/usr/bin/env python

# requires
# pip install daemonize gdata

# from daemonize import Daemonize
from spreadsheet import Spreadsheet
from oled import Oled
from gaugette.rgbled import RgbLed
from gaugette.rotary_encoder import RotaryEncoder
from gaugette.switch import Switch
import wiringpi
import time
import datetime
#import gdata.service # for exception handling
from gaugette.oauth import DeviceOAuth
import gaugette.gpio
import gaugette.spi

client_id = '911969952744.apps.googleusercontent.com'
client_secret = 'fj7nrIP3AeYDFQDbewnWrmfM'

pid = "/var/run/timeclock.pid"

# determine if we have an active project
# returns row_index, project_index
def active_project(ss, project_names):
    data = ss.get_range("Times!A2:C")
    row_index = None
    project_index = None
    if len(data)>0:
        last_row = data[-1] + ['','','']
        last_project_name, last_start, last_end = last_row[:3]
        if last_project_name.strip() and last_start.strip() and not last_end.strip():
            try:
                project_index = project_names.index(last_project_name)
                row_index = len(data) + 1 # 1-based for A1 addressing
            except ValueError:
                pass
    return row_index, project_index

def main():

    SPI_BUS = 0
    SPI_DEVICE = 0

    gpio = gaugette.gpio.GPIO()
    spi = gaugette.spi.SPI(SPI_BUS, SPI_DEVICE)

    RGB_PIN_R = 6
    RGB_PIN_G = 5
    RGB_PIN_B = 4

    startup_sequence      = [[50,0,0,500],[50,50,0,500],[0,50,0,500],[0,50,50,500],[0,0,50,500],[50,0,50,500]]
    boot_sequence         = [[100,100,100]]
    active_sequence       = [[0,0,50,2000],1000,[0,0,5,2000],600]
    going_active_sequence = [[0,0,50,0],[0,0,1,200],[0,0,50,200]]
    idle_sequence         = [[1,0,1]]
    going_idle_sequence   = [[50,0,50,0],[1,0,1,200],[50,0,50,200]]

    rgbled = RgbLed.Worker(gpio, RGB_PIN_R, RGB_PIN_G, RGB_PIN_B)
    rgbled.set_sequence(boot_sequence)
    rgbled.start()

    ENCODER_PIN_A  = 7
    ENCODER_PIN_B  = 8
    encoder = RotaryEncoder.Worker(gpio, ENCODER_PIN_A, ENCODER_PIN_B)
    encoder.start()

    SWITCH_PIN = 9
    switch = Switch(gpio, SWITCH_PIN)
    switch_state = switch.get_state()

    oled = Oled(gpio, spi)
    contrast = 0
    oled.ssd1306.set_contrast(contrast)

    rgbled.set_sequence(startup_sequence)

    # callback on first run to show validation code
    def on_user_code(user_code, validation_url):
        from gaugette.fonts import arial_24
        oled.ssd1306.clear_display()
        oled.ssd1306.draw_text3(0,0,user_code,arial_24)
        oled.ssd1306.display()

    oauth = DeviceOAuth(client_id, client_secret)
    token = oauth.get_token(on_user_code)
    credentials = oauth.get_credentials()

    SPREADSHEET_NAME     = 'TimeClock'
    SPREADSHEET_TEMPLATE = 'timeclock.template.json'
    ss = Spreadsheet(credentials)
    ss.open(SPREADSHEET_NAME, SPREADSHEET_TEMPLATE)

    data = ss.get_range("Projects!A2:A")
    project_names = [row[0] for row in data]
    if len(project_names) == 0:
        project_names = ['No projects defined','Update spreadsheet']

    oled.set_list(project_names)

    active_row_index, active_project_index = active_project(ss, project_names)

    if active_project_index != None:
        oled.list.scroll(active_project_index*oled.list.rows)
        rgbled.set_sequence(active_sequence)
    else:
        rgbled.set_sequence(idle_sequence)

    idle_counter = 0
    idle = True

    while True:
        time.sleep(0.01)
        delta = encoder.get_steps()

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
            date_format = "%Y-%m-%d %H:%M:%S"
            now = datetime.datetime.now().strftime(date_format)
            if not switch_state:
                selected = oled.list.align()

                start_line = active_row_index == None or selected != active_project_index
                # If there is an open record end it
                if active_row_index:
                    rgbled.set_sequence(going_idle_sequence)
                    end_time = now
                    range_name = "Times!C%d:D%d" % (active_row_index, active_row_index)
                    elapsed = "=INT( (C%d - B%d) * 60*24 )" % (active_row_index, active_row_index)
                    ss.set_range(range_name, [[end_time, elapsed]])
                    active_row_index = None

                # if either there was an open row, or a new project is selected
                if start_line:
                    active_project_index = selected
                    rgbled.set_sequence(going_active_sequence)
                    project_name = project_names[active_project_index]
                    start_time = now
                    result = ss.append_range("Times!A:D", [[project_name, start_time]])
                    updated_range = ss.parse_range(result['updates']['updatedRange'])
                    active_row_index = updated_range.row1

                if active_row_index:
                    rgbled.set_sequence(active_sequence)
                else:
                    rgbled.set_sequence(idle_sequence)

                idle = True


#daemon = Daemonize(app="timeclock", pid=pid, action=main)
#daemon.start()
main()
