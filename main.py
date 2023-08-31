import json
import time
import random
import winsound
import shutil
import os
import sys
from zipfile import ZipFile

import requests
from PIL import ImageGrab
from PIL import ImageChops
import pyautogui
import screen_brightness_control as sbc
import keyboard


def IndexOfImage(imageArray, img):
    for i in range(len(imageArray)):
        if not ImageChops.difference(img, imageArray[i]).getbbox():
            return i
    return -1


def Pause():
    print('[System] Program paused')
    response = pyautogui.confirm(text='Select option on how to continue', title='Program paused', buttons=['Continue', 'Exit'])
    if response == 'exit':
        sys.exit()

def Alert(msg, silent=False):
    print('[Alert]', msg)
    sbc.set_brightness(30)
    winsound.PlaySound('alert_sound.wav', winsound.SND_LOOP|winsound.SND_ASYNC)

    response = pyautogui.confirm(text=msg, title='Select option on how to continue', buttons=['Continue', 'Pause', 'Exit'])

    winsound.PlaySound(None, 0)

    if response == 'pause':
        Pause()
    elif response == 'exit':
        sys.exit()

    sbc.set_brightness(0)


#reload and wait page on left or right of screen (0, 1), return True or False if successful
def ReloadAndWait(window):
    print('[System] Reloading {} window'.format('Premium' if window == 0 else 'Rsa'))
    pyautogui.click(loc_reload[window])
    time.sleep(0.5)
    pyautogui.moveTo(loc_mousehide[window])

    i = 6000

    time.sleep(0.5)
    while ImageChops.difference(ImageGrab.grab(bbox=bb_reload[window]), img_reload_initial[window]).getbbox() and i > 0:
        print('[System] {} window has not loaded yet, waiting'.format('Premium' if window == 0 else 'Rsa'), str(i), 'more seconds')
        i -= 1
        time.sleep(1)

    return i > 10


def Wait(seconds):
    print('[System] Waiting', str(seconds), 'seconds')
    target = time.time() + seconds
    while time.time() < target:
        if keyboard.is_pressed('p'):
            Pause()
        #time.sleep(0.5)

#keep track of each rows id and premium status. each iteration retrieve new trip info then for each premium trip found check if it was present in last iteration
#if not then alert user
#
def MonitorWindow():
    img_names = [0] * prem_num_rows
    img_icons = [0] * prem_num_rows
    img_names_last = [0] * prem_num_rows
    img_icons_last = [0] * prem_num_rows

    img_rsa = [0] * rsa_num_rows
    img_rsa_last = [0] * rsa_num_rows

    num_refreshes = 0

    pyautogui.click(loc_mousehide[0])
    for i in range(0, prem_num_rows):
        img_names[i] = ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i))
        img_icons[i] = ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i))

    pyautogui.click(loc_mousehide[1])
    for i in range(0, rsa_num_rows):
        img_rsa[i] = ImageGrab.grab(bbox=(bb_rsa[0], bb_rsa[1] + rsa_row_height * i, bb_rsa[2], bb_rsa[3] + rsa_row_height * i))

    while True:
        realign()
        play_alert = False
        linesfound = []
        img_names_last = img_names.copy()
        img_icons_last = img_icons.copy()
        pyautogui.click(loc_mousehide[0])
        for i in range(0, prem_num_rows):
            img_names[i] = ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i))
            img_icons[i] = ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i))

            #just look for empty image. ned to make custom index of function to check for image equality.
            # row contains premium trip where it did not before
            if ImageChops.difference(img_blank, img_icons[i]).getbbox():
                print('[Debug] Trip on row', str(i), 'is premium, previously found on row ', end='')
                img_old_index = IndexOfImage(img_names_last, img_names[i])
                print(str(img_old_index))
                # trip existed before but was not premium
                if img_old_index > -1:
                    if not ImageChops.difference(img_icons_last[img_old_index], img_blank).getbbox():
                        play_alert = True
                        linesfound.append(i + 1)
                        #Alert("Trip went Premium")
                    #else:
                        #Alert('Trip stayed premium')
                else:
                    play_alert = True
                    linesfound.append(i + 1)
                    #Alert("New Premium trip added")

        if play_alert:
            Alert('Premium trip found on line(s) {}'.format(str(linesfound)))

        print(f'[System] Refresh count: {num_refreshes}')
        Wait(random.randrange(10, 50))
        ReloadAndWait(0)

        num_refreshes = num_refreshes + 1

        if num_refreshes % rsa_interval == 0 and option_monitor_rsa:
            realign()
            img_rsa_last = img_rsa.copy()
            pyautogui.click(loc_mousehide[1])
            for i in range(0, rsa_num_rows):
                img_rsa[i] = ImageGrab.grab(bbox=(bb_rsa[0], bb_rsa[1] + rsa_row_height * i, bb_rsa[2], bb_rsa[3] + rsa_row_height * i))
                img_old_index = IndexOfImage(img_rsa_last, img_rsa[i])
                if img_old_index == -1 and ImageChops.difference(rsa_blank, img_rsa[i]).getbbox():
                    play_alert = True
                    linesfound.append(i + 1)

            if play_alert:
                Alert('Rsa found on line(s) {}'.format(str(linesfound)))

            print(f'[System] Refresh count: {num_refreshes}')
            Wait(random.randrange(10, 50))
            ReloadAndWait(1)
            num_refreshes = num_refreshes + 1

def realign():
    # find vertical offset
    pyautogui.click(loc_mousehide[0])
    img_vertprobe = ImageGrab.grab(bbox=bb_prem_vertprobe)
    for y in range(0, 100):
        if img_vertprobe.getpixel((0, y)) == (128, 128, 128): # color of top of table
            if y != prem_vertprobe_goal:
                prem_vertical_offset = y - prem_vertprobe_goal
                bb_prem_name[1] += prem_vertical_offset
                bb_prem_name[3] += prem_vertical_offset
                bb_prem_icon[1] += prem_vertical_offset
                bb_prem_icon[3] += prem_vertical_offset
            break


    img_horizprobe = ImageGrab.grab(bbox=(0, bb_prem_icon[1], 600, bb_prem_icon[1] + 1))
    for x in range(560, 450, -1):
        if img_horizprobe.getpixel((x, 0)) == (128, 128, 128):
            bb_prem_icon[0] = x - 20
            bb_prem_icon[2] = x - 10
            break

    pyautogui.click(loc_mousehide[1])
    img_vertprobe = ImageGrab.grab(bbox=bb_rsa_vertprobe)
    for y in range(0, 100):
        if img_vertprobe.getpixel((0, y)) == (128, 128, 128): # color of top of table
            if y != rsa_vertprobe_goal:
                rsa_vertical_offset = y - rsa_vertprobe_goal
                bb_rsa[1] += rsa_vertical_offset
                bb_rsa[3] += rsa_vertical_offset
            break


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

#==== main ====
VERSION = 'v1.0.8'
update()


print('[System] Waiting 10 seconds')
time.sleep(10)
print('[System] Performing setup')

#set up variables
night_cont = True
img_reload_initial = [None, None]
prem_vertical_offset = 0
rsa_vertical_offset = 0
loc_mousehide = [[50, 295], [737, 300]]
img_blank = None
rsa_blank = None

#load config file
with open('config.json', 'r') as file:
    config = json.load(file)
system_mode = 'dev' if pyautogui.size().width == 1920 else 'release'
print('[System] Loading in {} mode'.format(system_mode))

bb_reload = config[system_mode]['bb_reload']
loc_reload = config[system_mode]['loc_reload']
bb_prem_vertprobe = config[system_mode]['bb_prem_vertprobe']
prem_vertprobe_goal = config[system_mode]['prem_vertprobe_goal']
bb_prem_name = config[system_mode]['bb_prem_name']
bb_prem_icon = config[system_mode]['bb_prem_icon']
prem_row_height = config[system_mode]['prem_row_height']
prem_num_rows = config[system_mode]['prem_num_rows']
bb_rsa_vertprobe = config[system_mode]['bb_rsa_vertprobe']
rsa_vertprobe_goal = config[system_mode]['rsa_vertprobe_goal']
bb_rsa = config[system_mode]['bb_rsa']
rsa_row_height = config[system_mode]['rsa_row_height']
rsa_num_rows = config[system_mode]['rsa_num_rows']
option_monitor_rsa = config[system_mode]['monitor_rsa']

rsa_interval = config['rsa_interval']



realign()



if night_cont:
    sbc.set_brightness(0)

for i in range(0, prem_num_rows):
    ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i)).save('debug/name_{}.png'.format(i))
    ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i)).save('debug/icon_{}.png'.format(i))
for i in range(0, rsa_num_rows):
    ImageGrab.grab(bbox=(bb_rsa[0], bb_rsa[1] + rsa_row_height * i, bb_rsa[2], bb_rsa[3] + rsa_row_height * i)).save('debug/rsa_{}.png'.format(i))


pyautogui.click(loc_mousehide[0])
img_reload_initial[0] = ImageGrab.grab(bbox=bb_reload[0])
time.sleep(0.2)
pyautogui.click(loc_mousehide[1])
img_reload_initial[1] = ImageGrab.grab(bbox=bb_reload[1])
time.sleep(0.2)

img_blank = ImageGrab.grab(bbox=(bb_prem_icon[0] + 50, bb_prem_icon[1], bb_prem_icon[2] + 50, bb_prem_icon[3]))
img_blank.save('debug/blank.png')
rsa_blank = ImageGrab.grab(bbox=(bb_rsa[0] + 400, bb_rsa[1], bb_rsa[2] + 400, bb_rsa[3]))
rsa_blank.save('debug/rsa_blank.png')

print('[System] Setup complete')
MonitorWindow()


#==== end of program ====
