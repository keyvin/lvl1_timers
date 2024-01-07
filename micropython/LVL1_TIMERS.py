import ujson
import time
import math
import secrets

from neopixel import Neopixel
from machine import Pin
from machine import PWM
import network
from utime import sleep, ticks_ms, ticks_diff
import urequests
import socket


CLEAR_SAVED = True

BUZZ_ENABLED = True
BUZZ_EVERY=10
BUZZ_FREQ=5
BUZZ_LEN=100
BOARD_PULL_UP = True

PWM_PIN=28

REPORT_TO_IP = "192.168.0.126"
REPORT_TO_PORT = 31230


BRIGHT=128
DEBOUNCE = 2   #in MS
PRESS = 3000   #longpress is 3 seconds



TIMER_1_NAME = "LASER LENS CLEAN"
TIMER_1_UNIT = "DAYS"
TIMER_1_ENABLED = True
TIMER_1_PERIOD = 12
#pixperday can (and oftenw will) be a fraction
TIMER_1_PIXPERDAY = 1       
TIMER_1_CURRENT = 0
TIMER_1_TONE = 800
TIMER_1_NORMAL_COLOR = (255,0,0)
TIMER_1_ALERT_COLOR = (0,0,255)
#pixels are the total number of pixels in indicator. PIXPERDDAY*PERIOD Should be close to this number
TIMER_1_PIXELS = 12    
TIMER_1_PIN = 27



TIMER_2_NAME = "LASER FILTER CLEAN"
TIMER_2_UNIT = "HOURS"
TIMER_2_ENABLED = True
TIMER_2_PERIOD = 12
TIMER_2_PIXPERDAY = 1
TIMER_2_CURRENT = 0
TIMER_2_TONE = 800
TIMER_2_NORMAL_COLOR = (255,255,0)
TIMER_2_ALERT_COLOR =  (0,0,255)
TIMER_2_PIXELS = 12
TIMER_2_PIN = 22


TIMER_3_NAME = "LASER DEBRIS CLEAN"
TIMER_3_UNIT = "HOURS"
TIMER_3_ENABLED = True
TIMER_3_PERIOD = 12
TIMER_3_PIXPERDAY = 1
TIMER_3_CURRENT = 0
TIMER_3_TONE = 800
TIMER_3_NORMAL_COLOR = (255,0,0)
TIMER_3_ALERT_COLOR = (0,0,255)
TIMER_3_PIXELS = 12
TIMER_3_PIN = 18

T1_DEFAULT = {"NAME": TIMER_1_NAME, "PERIOD": TIMER_1_PERIOD, "CURRENT": TIMER_1_CURRENT,
      "TONE":TIMER_1_TONE, "NORMAL_COLOR":TIMER_1_NORMAL_COLOR,
      "ALERT_COLOR":TIMER_1_ALERT_COLOR, "PIXPERDAY": TIMER_1_PIXPERDAY,
              "PIXELS":TIMER_1_PIXELS,"OVERDUE":False, "PIN":TIMER_1_PIN, "FILE_NAME":"/t1.json", "ENABLED":TIMER_1_ENABLED, "TIME_UNIT":TIMER_1_UNIT}

T2_DEFAULT = {"NAME": TIMER_2_NAME, "PERIOD": TIMER_2_PERIOD, "CURRENT": TIMER_2_CURRENT,
      "TONE":TIMER_2_TONE, "NORMAL_COLOR":TIMER_2_NORMAL_COLOR,
      "ALERT_COLOR":TIMER_2_ALERT_COLOR, "PIXPERDAY": TIMER_2_PIXPERDAY, "PIXELS":TIMER_2_PIXELS, "OVERDUE":False,
              "PIN":TIMER_2_PIN, "FILE_NAME":"/t2.json", "ENABLED":TIMER_2_ENABLED, "TIME_UNIT":TIMER_2_UNIT}
 
T3_DEFAULT = {"NAME": TIMER_3_NAME, "PERIOD": TIMER_3_PERIOD, "CURRENT": TIMER_3_CURRENT,
      "TONE":TIMER_3_TONE, "NORMAL_COLOR":TIMER_3_NORMAL_COLOR,
      "ALERT_COLOR":TIMER_3_ALERT_COLOR, "PIXPERDAY": TIMER_3_PIXPERDAY, "PIXELS":TIMER_3_PIXELS,
              "OVERDUE":False, "PIN":TIMER_3_PIN, "FILE_NAME":"/t3.json", "ENABLED":TIMER_3_ENABLED, "TIME_UNIT":TIMER_3_UNIT}


class Button():
    def __init__(self, pin, push_function, debounce_ms=DEBOUNCE, long_press_ms=PRESS, pullup=BOARD_PULL_UP):
        if pullup == True:
            self.button = [machine.Pin(pin,Pin.IN, Pin.PULL_UP), 1,0]
            self.active = 0
        else:
            self.button = [machine.Pin(pin,Pin.IN, Pin.PULL_DOWN),0,0]
            self.active = 1
        self.push_function = push_function
        self.debounce_ms = debounce_ms
        self.long_press_ms = long_press_ms
    
    def check(self):
        global MUTE
        curr_ms = time.ticks_ms()
        current = self.button[0].value()
        time_diff = time.ticks_diff(curr_ms, self.button[2])
    #if button state does not match last state
        if current != self.button[1]:
            if current != self.active:     #if transitioning from pressed to not press
                if time_diff < self.debounce_ms:     #software debounce
                    pass  #not steady yet
                elif time_diff < self.long_press_ms:      #held for less than hardpress. 
                    self.button[1] = current      #todo mute beeper for day on softpress
                    self.button[2] = curr_ms
                    MUTE = True
                    print ("Mute")
                else:
                    self.button[1] = current      #hard press, report button press
                    if self.push_function:
                        self.push_function()
                    return(True)
            elif current == self.active:               #transition high to low, mark button held and ms_tick when pressed
                self.button[1] = 0                		#bouncing doesn't matter. 
                self.button[2] = curr_ms 
        return False

class MaintenanceTimer:
    def __init__(self, file_name, defaults, clear_saved=CLEAR_SAVED):
        self.file_name = file_name
        self.clear_save_data = clear_saved
        self.timer = {}
        self.alert_light_toggle = False
        if self.clear_save_data:
            self.timer = defaults
        else:
            self.load_timer()

#loads timers. JSON file needs to be deleted if defaults changed. 
    def load_timer(self):
        try:
            data = open(self.file_name,'r')
            f = data.read()
            data.close()
            self.timer = ujson.loads(f)
            print("Loaded: " + file_name)
        except:
            self.timer = default
        set_pixels(timer["PIN"], timer["NORMAL_COLOR"], timer["PIXELS"], math.floor(timer["CURRENT"]*timer["PIXPERDAY"]))
        return self.timer


#simple function to save data from json file in flash
#used to checkpoint count of days on timers if power lost
#no rtc.
    def save_timer(self):   
        try:
            file = open(self.file_name,'w')
            file.write(ujson.dumps(self.timer))
            file.close()
        except:
            print('File error')
            pass #nothing to be done really
    
    def reset_timer(self):
        self.timer["OVERDUE"] = False
        self.timer["CURRENT"] = 0
        self.save_timer()
        timer = self.timer
        set_pixels(timer["PIN"], timer["NORMAL_COLOR"], timer["PIXELS"], math.floor(timer["CURRENT"]*timer["PIXPERDAY"]))

    def tick_timer(self, current_second):
        if self.timer["ENABLED"] == True:
            current_unit = self.timer["CURRENT"]
            interval = self.timer["PERIOD"]
            current_unit = current_unit + 1
            self.timer["CURRENT"] = current_unit
            if current_unit > interval:
                self.timer["OVERDUE"] = True
            set_pixels(self.timer["PIN"], self.timer["NORMAL_COLOR"], self.timer["PIXELS"], math.floor(self.timer["CURRENT"]*self.timer["PIXPERDAY"]))
            self.save_timer()
            if self.timer["OVERDUE"]==True:    #if Timer is overdue, flash indicator
                if seconds%30==0:    #Flip color every 30 seconds.   
                    self.alert_light_toggle = not self.alert_light_toggle
                    if self.alert_light_toggle:
                        set_pixels(self.timer["PIN"], self.timer["ALERT_COLOR"], self.timer["PIXELS"], self.timer["PIXELS"])
                    else:
                        set_pixels(self.timer["PIN"], self.timer["NORMAL_COLOR"], self.timer["PIXELS"],self.timer["PIXELS"])
            report_to_server(ujson.dumps(i.timer))
            
            
    def can_tick_minutes(self):
        return self.timer["TIME_UNIT"] == "MINUTES"
    
    
    def can_tick_hours(self):
        return (self.timer["TIME_UNIT"] == "HOURS")
    
    def can_tick_days(self):
        return self.timer["TIME_UNIT"] == "DAYS"
    def overdue(self):
        return self.timer["OVERDUE"]

class Buzzer():
    def __init__(self, pin, hz, enabled=BUZZ_ENABLED, frequency_in_seconds=BUZZ_FREQ, length_ms=BUZZ_LEN):
        self.second_tick_last_turned_on = 0
        self.tone = hz
        self.hz = 0
        self.pwm = PWM(Pin(pin))
        self.length_ms = length_ms
        self.frequency_in_seconds = frequency_in_seconds
        self.second_tick_last_turned_on = 0
        self.pwm.duty_u16(0)    
        self.on = False
        self.buzzer_start_time_ms = 0
        self.enabled=enabled
    def do_buzz(self, time_s, overdue=False):
        global MUTE
        time_ms = time.ticks_ms()
        if (not MUTE) and self.enabled and overdue:
            if self.on:
                if time.ticks_diff(time_ms, self.buzzer_start_time_ms) > self.length_ms:
                    self.pwm.duty_u16(0)
                    self.on = False
            else:
                if time_s < self.second_tick_last_turned_on:
                    self.second_tick_last_turned_on = time_s
                    return
                if (time_s - self.second_tick_last_turned_on) > self.frequency_in_seconds:
                    self.on = True
                    self.second_tick_last_turned_on = time_s
                    self.buzzer_start_time_ms = time.ticks_ms()
                    self.pwm.freq(self.tone)
                    self.pwm.duty_u16(32768)
                
        


#simple function to reset strip, set brightness, and draw pixels. 
def set_pixels(pin, color, num_pixels, to_set):
    if to_set > num_pixels:
        to_set = num_pixels
    pixels = Neopixel(num_pixels, 0, pin, "GRB")
    pixels.fill((0,0,0))
    pixels.brightness(BRIGHT)
    for i in range(to_set):
        pixels.set_pixel(i, color)
    pixels.show()


def report_to_server(json_to_send):
    try:
        sockaddr = socket.getaddrinfo(REPORT_TO_IP, REPORT_TO_PORT)[0][-1]
        s = socket.socket()
        s.connect(sockaddr)
        s.write(json_to_send)
        s.close()
    except:
        print("Netowrk Failure")

def connect_to_wifi():
    try:
        wlan.active(True)
        wlan.connect(secrets.SSID, secrets.WPA)
        print(wlan.status())
        print(wlan.isconnected())
        #wlan.ifconfig(['192.168.0.205', '255.255.255.0', '192.168.0.1','8.8.8.8'])
        print('network config:', wlan.ifconfig())
    except:
        print("Network Connection Failed.")   

#timekeeping
curr_ms = 0
last_ms =0
seconds = 0
hours = 0
days =0

#One second tick and 24 hour tick 
tick_timers=False
sec_tick=False
hours_tick=False
days_tick=False
#buzzer variables
MUTE=False       #h 
overdue = False  #should timer sound
buzz_on = False  #Buzz on means it is on.
buzz_length = 0  #how long buzzer has been on. 
wlan = network.WLAN(network.STA_IF)
print("Start!")
connect_to_wifi()


#init
#holds timers
timers = []

timers.append(MaintenanceTimer('/t1.json', T1_DEFAULT, CLEAR_SAVED))
timers.append(MaintenanceTimer('/t2.json', T2_DEFAULT, CLEAR_SAVED))
timers.append(MaintenanceTimer('/t3.json', T3_DEFAULT, CLEAR_SAVED))
#sets neopixels
for timer in timers:    
    print(timer)

buttons = []
buttons.append(Button(0, timers[0].reset_timer))
buttons.append(Button(1, timers[1].reset_timer))
buttons.append(Button(2, timers[2].reset_timer))

for button in buttons:
    print(button)

buzz = Buzzer(28, 800)

#main loop
while True:
    #simple jiffy clock (no RTC)
    curr_ms = time.ticks_ms()
    #process events once a second
    if time.ticks_diff(curr_ms, last_ms) > 1000: #one second has passed
        last_ms = curr_ms
        seconds = seconds +1
        sec_tick = True #handle once per second tasks
        if seconds >= 3600:
            seconds = 0
            hours = hours +1
            hours_tick=True
            if hours > 23:
                MUTE = False       #unmute buzzer
                hours = 0
                days = days + 1
                days_tick = True
    #handle button presses and checkpoint press
    #will call the timer callback to clear timer if set.
    for i in buttons:
        i.check()
    
    #most events only need to be processed every second.
    #theoretically could sleep the CPU till just before next second
    if sec_tick==True:
        if days_tick:
            MUTE = False
            for timer in timers:
                if timer.can_tick_days():
                    timer.tick_timer(seconds)
            days_tick = False
        
        #test network connection every three hours, report every two. 
        if hours_tick==True:
            for i in timers:
                if i.can_tick_hours():
                    i.tick_timer(seconds)             
                    
            if hours%2==0:
                if not wlan.status():
                    connect_to_wifi()
            hours_tick = False
        overdue = False
        for i in timers:
            if timer.overdue():
                overdue = True        
        sec_tick= False
    
      
    buzz.do_buzz(seconds,overdue)
