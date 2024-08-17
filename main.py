import re
import json
import time
import random
import winsound
import shutil
import os
import sys
from zipfile import ZipFile

from PIL import ImageGrab
from PIL import ImageChops
import pyperclip
import keyboard
import pyautogui
import winsound
import requests
import screen_brightness_control as sbc

re_cap = re.compile(r"CA\s+Open")
re_intl = re.compile(r"DUB|EDI|LHR|LGW|CDG|AMS")
re_pair = re.compile(r"(Pairing # (?P<tripid>[\w\d]+) :.*?Crew:\s+(?P<cap>Open|.+?\n)(?=(Pairing|$)))")
par_ignored = ['NONE']
loc_par_details = [1150, 710]
loc_par_table = [1500, 500]

re_prem = re.compile(r"(^(\w{5})\s+(\w+)\s+\d+\s+(\d{2}:\d{2}).*?X.*?$)")
prem_ignored = ['NONE']
loc_prem_refresh = [120, 70]
loc_prem_table = [600, 600]

night_cont = False

def Pause():
    print('[System] Program paused')
    response = pyautogui.confirm(text='Select option on how to continue', title='Program paused', buttons=['Continue', 'Exit'])
    if response == 'Exit':
        sys.exit()
        os._exit()
        quit()
        exit()

def Wait(seconds):
    target = time.time() + seconds
    while time.time() < target:
        if keyboard.is_pressed('p'):
            Pause()
        #time.sleep(0.5)

#reload and wait page on left or right of screen (0, 1), return True or False if successful
def ReloadAndWait(window):
    print('[System] Reloading {} window'.format('Premium' if window == 0 else 'Rsa'))
    pyautogui.click(loc_reload[window])
    time.sleep(0.5)
    pyautogui.moveTo(loc_prem_table)

    i = 6000

    time.sleep(0.5)
    while ImageChops.difference(ImageGrab.grab(bbox=bb_reload[0]), img_reload_initial).getbbox() and i > 0:
        print('[System] {} window has not loaded yet, waiting'.format('Left' if window == 0 else 'Right'), str(i), 'more seconds')
        i -= 1
        time.sleep(1)

    return i > 10


def par_filter(x):
    if not re_cap.search(x[2]) == None and not x[1] in par_ignored and re_intl.search(x[0]) == None:
        return True
    else:
        return False

def get_pairings():
    global par_ignored

    pyautogui.click(loc_par_details)
    time.sleep(0.5)

    pyautogui.click(loc_par_table)
    keyboard.press_and_release('ctrl + a, ctrl + c')
    time.sleep(0.5)

    data = pyperclip.paste()
    matches = re.findall(r"(Pairing # (?P<tripid>[\w\d]+) :.*?Crew:\s+(?P<cap>Open|.+?\n)(?=(Pairing|$)))", data, re.S)
    filtered_list = filter(par_filter, matches)
    trip_ids = [x[1] for x in filtered_list]
    trip_ids_str = '\n'.join(trip_ids)

    par_ignored += trip_ids

    print(trip_ids)
    if len(trip_ids) == 0:
        return

    winsound.PlaySound('alert_sound.wav', winsound.SND_LOOP|winsound.SND_ASYNC)
    choice = pyautogui.confirm(text=f"found {len(trip_ids)} trips\n" +trip_ids_str, title='Parings Found', buttons=['Highlight Next', 'Ignore All'])
    winsound.PlaySound(None, 0)

    if choice == 'Ignore All':
        return

    for trip in trip_ids:
        pyautogui.click(loc_par_table)
        pyperclip.copy("Pairing # " + trip)
        keyboard.press_and_release('ctrl + f, ctrl + v, enter')
        choice = pyautogui.confirm(text="Currently highlighted " + trip, title='Pairings Found', buttons=['Highlight Next', 'Ignore Remaining'])

        if choice == 'Ignore Remaining':
            break

    choice = pyautogui.confirm(text="Would you like to resume", title='Parings Found', buttons=['Continue', 'Pause', 'Quit'])

    if choice == 'Quit':
        quit()
    elif choice == 'Pause':
        Pause()

def prem_filter(x):
    if re_intl.search(x[0]) == None and not x[1] in prem_ignored:
        return True
    else:
        return False

def get_premium():
    global prem_ignored

    # refresh and wait
    pyautogui.click(loc_prem_refresh)
    time.sleep(2)

    pyautogui.click(loc_prem_table)
    keyboard.press_and_release('ctrl + a, ctrl + c')
    time.sleep(0.5)

    data = pyperclip.paste()
    matches = re.findall(r"(^(\w{5})\s+(\w+)\s+\d+\s+(\d{2}:\d{2}).*?X.*?$)", data, re.M)
    filtered_list = filter(prem_filter, matches)

    trip_id_dates = [x[1] + " " + x[2] for x in filtered_list]
    trips = '\n'.join(trip_id_dates)
    prem_ignored += trip_id_dates

    if len(trip_id_dates) == 0:
        return

    winsound.PlaySound('alert_sound.wav', winsound.SND_LOOP|winsound.SND_ASYNC)
    choice = pyautogui.confirm(text=f"found {len(trip_id_dates)} trips\n" + trips, title='Premium Found', buttons=['Ignore', 'Pause', 'Quit'])
    winsound.PlaySound(None, 0)

    if choice == 'Pause':
        Pause()

def update():
    print(f'[System] Checking for updates, current version {VERSION}')

    dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    if os.path.exists(f'{dir}\\temp'):
        shutil.rmtree(f'{dir}\\temp')

    url = "https://api.github.com/repos/pokeylink227/godzilla/releases/latest"
    response = requests.get(url)

    if response.json()['tag_name'] > VERSION:
        print('[System] Update found')
        r = requests.get(response.json()['assets'][0]['browser_download_url'])
        f = open('update.zip','wb')
        f.write(r.content)
        f.close()

        with ZipFile('update.zip') as zpf:
            zpf.extractall()

        shutil.move(f'{dir}\\main\\main', f'{dir}\\temp')

        f = open(f'{dir}/upd.bat', 'w')
        f.write(f'@echo off  \ncd {dir}\nrmdir /s /q {dir}\\main  \ntimeout 2 >nul\nrename {dir}\\temp main  \ntimeout 2 >nul\ndel {dir}\\upd.bat') #add absolute paths
        f.close()
        os.startfile(f'{dir}/upd.bat')

        sys.exit()
    print('[System] Program up to date')

def main():
    time.sleep(5)

    cycle = 0

    while True:
        get_pairings()
        if cycle % 3 == 0:
            get_premium()

        time.sleep(random.randrange(15, 35))
        cycle += 1

#==== main ====
VERSION = 'v2.0.4'
update()


if night_cont:
    sbc.set_brightness(0)

print('[System] Waiting 10 seconds')
time.sleep(10)
print('[System] Performing setup')

#load config file
with open('config.json', 'r') as file:
    config = json.load(file)
system_mode = 'dev' if pyautogui.size().width == 1920 else 'release'
print('[System] Loading in {} mode'.format(system_mode))

loc_prem_refresh = config[system_mode]['loc_prem_refresh']
loc_prem_table = config[system_mode]['loc_prem_table']

loc_par_details = config[system_mode]['loc_par_details']
loc_par_table = config[system_mode]['loc_par_table']

bb_reload = config[system_mode]['bb_reload']

img_reload_initial = ImageGrab.grab(bbox=bb_reload[0])
time.sleep(0.2)

main()
