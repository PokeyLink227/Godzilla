import json
import time
import random
import winsound

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
        exit()

def Alert(msg, silent=False):
    print('[Alert]', msg)
    sbc.set_brightness(30)
    winsound.PlaySound('alert_sound.wav', winsound.SND_LOOP|winsound.SND_ASYNC)

    response = pyautogui.confirm(text=msg, title='Select option on how to continue', buttons=['Continue', 'Pause', 'Exit'])

    winsound.PlaySound(None, 0)

    if response == 'pause':
        Pause()
    elif response == 'exit':
        exit()

    sbc.set_brightness(0)


#reload and wait page on left or right of screen (0, 1), return True or False if successful
def ReloadAndWait(window):
    print('[System] Reloading {} window'.format('Premium' if window == 0 else 'Rsa'))
    pyautogui.click(loc_reload[window])
    time.sleep(0.5)
    pyautogui.moveTo(loc_mousehide)

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

    num_refreshes = 0

    for i in range(0, prem_num_rows):
        img_names[i] = ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i))
        img_icons[i] = ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i))

    while True:
        play_alert = False
        linesfound = []
        img_names_last = img_names.copy()
        img_icons_last = img_icons.copy()
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

        Wait(random.randrange(10, 50))
        ReloadAndWait(0)

        num_refreshes = num_refreshes + 1

        if num_refreshes % 5 == 0:
            Wait(random.randrange(10, 50))
            pyautogui.click(loc_reload[1])
            pyautogui.click(loc_mousehide)



def update():
    print('[System] Checking for updates')
    VERSION = 'v1.0'

    url = "https://api.github.com/repos/pokeylink227/godzilla/releases/latest"
    response = requests.get(url)

    if response.json()['tag_name'] > VERSION:
        print('[System] Update found')
        r = requests.get(response.json()['assets'][0]['browser_download_url'])
        f = open('update.zip','wb')
        f.write(r.content)

        with ZipFile("update.zip") as zpf:
            zpf.extractall()

        shutil.move('main', '../temp')
        shutil.rmtree('../main')
        os.rename('../temp', '../main')
        print('[System] Update installed')
        exit()
    print('[System] Program up to date')

#==== main ====
update()
print('[System] Waiting 5 seconds')
time.sleep(5)
print('[System] Performing setup')

#set up variables
night_cont = True
img_reload_initial = [None, None]
vertical_offset = 0
loc_mousehide = [50, 295]
img_blank = None
bb_rsa = None

#load config file
with open('config.json', 'r') as file:
    config = json.load(file)
system_mode = 'dev' if pyautogui.size().width == 1920 else 'release'
print('[System] Loading in {} mode'.format(system_mode))

bb_reload = config[system_mode]['bb_reload']
loc_reload = config[system_mode]['loc_reload']
bb_vertprobe = config[system_mode]['bb_vertprobe']
vertprobe_goal = config[system_mode]['vertprobe_goal']
bb_prem_name = config[system_mode]['bb_prem_name']
bb_prem_icon = config[system_mode]['bb_prem_icon']
prem_row_height = config[system_mode]['prem_row_height']
prem_num_rows = config[system_mode]['prem_num_rows']




# find vertical offset
img_vertprobe = ImageGrab.grab(bbox=bb_vertprobe)
for y in range(0, 100):
    if img_vertprobe.getpixel((0, y)) == (128, 128, 128): # color of top of table
        if y != vertprobe_goal:
            vertical_offset = y - vertprobe_goal
            bb_prem_name[1] += vertical_offset
            bb_prem_name[3] += vertical_offset
            bb_prem_icon[1] += vertical_offset
            bb_prem_icon[3] += vertical_offset
        break


if night_cont:
    sbc.set_brightness(0)

for i in range(0, prem_num_rows):
    ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i)).save('debug/name_{}.png'.format(i))
    ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i)).save('debug/icon_{}.png'.format(i))

pyautogui.click(loc_mousehide)


img_reload_initial[0] = ImageGrab.grab(bbox=bb_reload[0]) # might need to account for window being focused or not
img_blank = ImageGrab.grab(bbox=(bb_prem_icon[0] + 50, bb_prem_icon[1], bb_prem_icon[2] + 50, bb_prem_icon[3]))
img_blank.save('debug/blank.png')

print('[System] Setup complete')
MonitorWindow()


#==== end of program ====
