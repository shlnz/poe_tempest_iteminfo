import json
import sys
import os
import winsound
import configparser
import psutil
import subprocess

from urllib.request import urlopen
from datetime import datetime, timedelta
from time import sleep


GREAT = {}
clear = lambda: os.system("cls")


def play_sound():
    fname = 'beep.wav'
    winsound.PlaySound(fname, winsound.SND_FILENAME)


def full_hour():
    ''' returns the next full hour '''
    return datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def current_time_str():
    ''' returns current time '''
    return datetime.now().strftime('%H:%M:%S')


def exit_with_input():
    ''' Exit the script with a user input '''
    input('Exit with any key')
    sys.exit()


def end_autohotkey(prog_path):
    ''' End AutoHotKey if already running '''
    procname = prog_path.split('\\')[-1]

    for proc in psutil.process_iter():
        if proc.name() == procname:
            proc.kill()


def print_great_temp():
    ''' Print great temps on screen '''
    print('')
    print('[%s] Good tempests:' % current_time_str())
    global GREAT
    for map_name, items in GREAT.items():
        print('------------------------------------')
        print('[%s] Map:          %s' % (current_time_str(), map_name))
        print('[%s] Votes:        %s' % (current_time_str(), items[2]))
        print('[%s] Tempest:      %s' % (current_time_str(), items[0]))
        print('[%s] Description:  %s' % (current_time_str(), items[1]))
    print('------------------------------------')


def get_current_tempests():
    ''' Open url to get tempest info and return it in a dict '''
    response = urlopen('http://poetempest.com/api/v1/current_tempests').read()
    return json.loads(response.decode('utf-8'))


def write_to_map_list(temps, file_to_start):
    ''' Getting information out of the MapList.txt in the script folder
        and replacing the new info with the existing MapList.txt in
        the data/MapList.txt '''
    try:
        new_file = ''

        with open('MapList.txt', 'r') as f:

            for line in f:

                if line == '':
                    new_file += line
                    continue

                for map_name, prefs in temps.items():

                    map_name = map_name.replace('_', ' ').title() + ' Map'
                    tempest_name = prefs['name']
                    base = prefs['base']
                    suffix = prefs['suffix']
                    votes = prefs['votes']
                    tempest_type = prefs['type']

                    if line.startswith('mapList["' + map_name):

                        line = line[:-2] + '`n`nTempest on map:`n- ' + tempest_name + '`n- ' + base

                        if suffix != '':
                            line += '`n- Suffix: ' + suffix

                        if tempest_type != '':
                            line += '`n- Type: ' + tempest_type

                        if votes > 0:
                            line += '`n- Votes: ' + str(votes)

                        line += '"\n'

                new_file += line
    except IOError:
        print('[%s] ERROR: Could not find file "MapList.txt" in script folder.' % current_time_str())
        exit_with_input()

    try:
        with open(os.path.abspath(os.path.join(os.path.split(file_to_start)[0], 'data', 'MapList.txt')), 'w') as f:
            f.write(new_file)
    except IOError:
        print('[%s] ERROR: Could not find file "MapList.txt" from ItemInfo. Maybe you set the wrong path in the config.ini.' % current_time_str())
        exit_with_input()


def handle_great_tempests(temps, play_mp3):
    ''' print if there is a new great tempest on a map. resets every full hour '''
    new_great_temps = False

    global NEXT_FULL_HOUR
    global GREAT

    if datetime.now() > NEXT_FULL_HOUR:
        NEXT_FULL_HOUR = full_hour()
        GREAT = {}

    for map_name, prefs in temps.items():

        map_name = map_name.replace('_', ' ').title()
        tempest_name = prefs['name']
        base = prefs['base']
        votes = prefs['votes']
        tempest_type = prefs['type']

        if tempest_type == 'great' and map_name not in GREAT:
            GREAT[map_name] = [tempest_name, base, votes]
            new_great_temps = True

    if GREAT:
        print_great_temp()

    if play_mp3.lower() == 'on' and new_great_temps:
        play_sound()


def read_config():
    ''' reading in config file '''
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        auto_hot_key = config['Path']['AutoHotKey']
        file_to_start = config['Path']['ItemInfo']
        reload_time = int(config['RefreshInterval']['reload'])
        if reload_time < 1:
            reload_time = 1
        play_mp3 = config['PlaySounds']['play']
    except KeyError:
        config['Path'] = {'AutoHotKey': 'C:\\path\\to\\AutoHotKey.exe',
                          'ItemInfo': 'C:\\path\\to\\ItemInfo.ahk'}
        config['RefreshInterval'] = {'reaload': '5'}
        config['PlaySounds'] = {'play': 'True'}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print("Wrote new config.ini.\nYou need to adjust this config file first.")
        exit_with_input()

    return auto_hot_key, reload_time, file_to_start, play_mp3


if __name__ == '__main__':
    # TODO: READ LOGFILE FROM POE
    NEXT_FULL_HOUR = full_hour()
    prog_path, reload_time, file_to_start, play_mp3 = read_config()
    try:
        while True:
            clear()
            end_autohotkey(prog_path)
            print('[%s] Grabbing new data...' % current_time_str())
            temps_dict = get_current_tempests()
            handle_great_tempests(temps_dict, play_mp3)
            write_to_map_list(temps_dict, file_to_start)
            print('[%s] Done. Next try in %d min. Restarting "AutoHotKey"' % (current_time_str(), reload_time))
            subprocess.Popen([prog_path, file_to_start])
            sleep(reload_time * 60)
    except KeyboardInterrupt:
        end_autohotkey(prog_path)
