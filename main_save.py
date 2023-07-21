from PIL import ImageGrab
from PIL import ImageChops
import winsound
import time
import pyautogui
import random
import screen_brightness_control as sbc
import keyboard


night_cont = True

# make icon godzilla eating airplane
#name is godzilla
# make icon bbox smller to make faster

loc_mousehide = [50, 295]
img_blank = None

bb_prem_icon = [482, 470, 489, 477]
bb_prem_name = [97, 470, 171, 477]
prem_row_height = 25

bb_rsa = None

bb_reload = [[80, 54, 94, 68], [1040, 54, 1054, 68]]
img_reload_initial = [None, None]
loc_reload = [[87, 61], [1047, 61]]


#make loop index range non static
def IndexOfImage(imageArray, img):
    for i in range(len(imageArray)):
        if not ImageChops.difference(img, imageArray[i]).getbbox():
            return i
    return -1


def Pause():
    print('[Paused]')
    response = pyautogui.confirm(text='select option on how to continue', title='program paused', buttons=['continue', 'exit'])
    if response == 'exit':
        exit()

def Alert(msg, silent=False):
    print('[Alert]', msg)
    sbc.set_brightness(30)
    winsound.PlaySound('alert_sound.wav', winsound.SND_LOOP|winsound.SND_ASYNC)

    response = pyautogui.confirm(text=msg, title='select option on how to continue', buttons=['continue', 'pause', 'exit'])

    winsound.PlaySound(None, 0)

    if response == 'pause':
        Pause()
    elif response == 'exit':
        exit()

    sbc.set_brightness(0)


#reload and wait page on left or right of screen (0, 1), return True or False if successful
def ReloadAndWait(window):
    print('reloading')
    pyautogui.click(loc_reload[window])
    time.sleep(0.5)
    pyautogui.moveTo(loc_mousehide)

    i = 6000
    while not ImageGrab.grab(bbox=bb_reload[window]) == img_reload_initial[window] and i > 0:
        print("Page not loaded yet, waiting ", str(i), " more seconds.")
        i -= 1
        time.sleep(1)

    return i > 10


def Wait(seconds):
    sleep_time = random.randrange(10, 50)
    print('waiting', str(seconds), 'seconds until next refresh')

    target = time.time() + seconds
    while time.time() < target:
        if keyboard.is_pressed('p'):
            Pause()
        #time.sleep(0.5)

#keep track of each rows id and premium status. each iteration retrieve new trip info then for each premium trip found check if it was present in last iteration
#if not then alert user
#
def MonitorWindow():
    img_names = [0] * 13
    img_icons = [0] * 13
    img_names_last = [0] * 13
    img_icons_last = [0] * 13

    num_refreshes = 0

    for i in range(0, 13):
        img_names[i] = ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i))
        img_icons[i] = ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i))

    while True:
        play_alert = False
        linesfound = []
        img_names_last = img_names.copy()
        img_icons_last = img_icons.copy()
        for i in range(0, 13):
            img_names[i] = ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i))
            img_icons[i] = ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i))

            #just look for empty image. ned to make custom index of function to check for image equality.
            # row contains premium trip where it did not before
            if ImageChops.difference(img_blank, img_icons[i]).getbbox():
                print('trip on row', str(i), 'prem')
                img_old_index = IndexOfImage(img_names_last, img_names[i])
                print('old index:', str(img_old_index))
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
            Alert('Premium Trip Found on line(s) {}.'.format(str(linesfound)))

        sleep_time = random.randrange(10, 50)
        print('waiting', str(sleep_time), 'seconds until next refresh')
        time.sleep(sleep_time)
        ReloadAndWait(0)

        num_refreshes = num_refreshes + 1

        if num_refreshes % 5 == 0:
            sleep_time = random.randrange(10, 50)
            print('waiting', str(sleep_time), 'seconds until next refresh')
            time.sleep(sleep_time)
            pyautogui.click(loc_reload[1])
            pyautogui.click(loc_mousehide)



#==== main ====
state = "MONITORING"


while True:
    Wait(10)

print("waiting 5 sec")
time.sleep(5)
print("starting")

if night_cont:
    sbc.set_brightness(0)

for i in range(0, 13):
    ImageGrab.grab(bbox=(bb_prem_name[0], bb_prem_name[1] + prem_row_height * i, bb_prem_name[2], bb_prem_name[3] + prem_row_height * i)).save('name_{}.png'.format(i))
    ImageGrab.grab(bbox=(bb_prem_icon[0], bb_prem_icon[1] + prem_row_height * i, bb_prem_icon[2], bb_prem_icon[3] + prem_row_height * i)).save('icon_{}.png'.format(i))

pyautogui.click(loc_mousehide)


img_reload_initial[0] = ImageGrab.grab(bbox=bb_reload[0]) # might need to account for window being focused or not
img_blank = ImageGrab.grab(bbox=(bb_prem_icon[0]+100, bb_prem_icon[1], bb_prem_icon[2]+100, bb_prem_icon[3]))
img_blank.save('blank.png')
MonitorWindow()


screen_width, screen_height = pyautogui.size()

## main monitoring loop is
#1 reload page
#2 wait for page to fully load
#3 take capture of premium icon location
#4 if it appears different from last capture alert user
#5 wait for input and possibly move search area in order to avoid alerting twice
## monitor larger region and determine where change occurs, this allows blacklisting trips





##while True:
##    time.sleep(2)
##    pyautogui.moveTo(50, 50)
##
##while True:
##    sc_last = sc
##    sc = ImageGrab.grab(bbox=bb_region_1)
##    if sc_last != sc:
##        print("ahhh")




#winsound.Beep(1000, 100)#halts program, can be avoided by using a sound file
