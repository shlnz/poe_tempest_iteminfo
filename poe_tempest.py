import json
import sys
import os
import winsound
import configparser
import psutil
import subprocess
import winreg
import platform
import errno
import re
import requests

from urllib.request import urlopen
from datetime import datetime, timedelta
from time import sleep
from itertools import islice


GREAT = {}
clear = lambda: os.system("cls")


def play_sound():
    fname = 'beep.wav'
    winsound.PlaySound(fname, winsound.SND_FILENAME)


def next_full_hour():
    ''' returns the next full hour '''
    return datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)


def last_full_hour():
    ''' returns the next full hour '''
    return datetime.now().replace(minute=0, second=0, microsecond=0)


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
        NEXT_FULL_HOUR = next_full_hour()
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
        # auto_hot_key = config['Paths']['AutoHotKey']
        file_to_start = config['Paths']['ItemInfo']
        reload_time = int(config['RefreshInterval']['reload'])
        # poe_path = config['Paths']['poePath']
        if reload_time < 1:
            reload_time = 1
        play_mp3 = config['PlaySounds']['play']
    except KeyError:
        config['Paths'] = {'AutoHotKey': 'C:\\path\\to\\AutoHotKey.exe',
                           'ItemInfo': 'C:\\path\\to\\ItemInfo.ahk'}
        config['RefreshInterval'] = {'reaload': '5'}
        config['PlaySounds'] = {'play': 'on'}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        print("Wrote new config.ini.\nYou need to adjust this config file first.")
        exit_with_input()

    return reload_time, file_to_start, play_mp3


def read_config_part(topic, item):
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        value = config[topic][item]
    except KeyError:
        print("ERROR: Could not read [%s] %s from config.ini." % (topic, item))
        exit_with_input()

    return value


def verify_log_data_and_vote(map_name, base_name, suffix_name=None):
    response = urlopen('http://poetempest.com/api/v0/maps').read()
    maps = json.loads(response.decode('utf-8'))

    response = urlopen('http://poetempest.com/api/v0/tempests').read()
    tempests = json.loads(response.decode('utf-8'))

    # verify map correctness
    if map_name not in maps:
        return

    # verify bases correctness
    if base_name not in tempests['bases']:
        return

    # verify suffix correctness
    if suffix_name is not None:
        if suffix_name not in tempests['suffixes']:
            return
    else:
        suffix_name = 'none'

    # vote for tempest on map
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
    data = {'map': map_name, 'base': base_name, 'suffix': suffix_name}
    url = 'http://poetempest.com/api/v0/vote'
    response = requests.post(url, data=data, headers=headers)
    if response.status_code == requests.codes.ok:
        print('[%s] Voting successful for Map: %s, base: %s, suffix: %s' % (current_time_str, map_name, base_name, suffix_name))

    return


def delete_poe_log(path):
    try:
        os.remove(path)
        print('Logfile gone')
    except OSError:
        pass


def read_poe_log(path, last_pos=0):
    last_h = last_full_hour()
    next_h = next_full_hour()
    try:
        with open(path, 'r') as f:
            for i, line in enumerate(islice(f, last_pos, None)):
                # check if the chat message is still in the current hour
                date = line[:19].replace('/', ' ').replace(':', ' ').split(' ')
                date = datetime(*[int(i) for i in date])

                if last_h < date < next_h:
                    line = line[19:]
                    match = re.findall(r'[\d\/\:\ ]{10,}287 \[[\w\s]*\]\ [\&\#]*[\w\_\-]*\:\ TEMPEST[\:\ ]{2,}(.*?)[\,\;\ ]{2,}(.*?)$', line, re.DOTALL)
                    if match and len(match[0]) == 2:
                        # TODO: need to replace it with a regex
                        map_name, prefs = match[0]
                        map_name = map_name.replace(' ', '_').lower()
                        if 'of' in prefs.lower():
                            temps = prefs.split('of')
                            base = temps[0].lower().replace('tempest', '').strip()
                            suffix = temps[1].lower().strip()
                            verify_log_data_and_vote(map_name, base, suffix)
                        elif 'none' in prefs.lower():
                            verify_log_data_and_vote(map_name, 'none')
                        else:
                            temps = prefs.lower().lstrip().split(' ')
                            base = temps[0].strip()
                            verify_log_data_and_vote(map_name, base)

            last_pos += i

        return last_pos
    except IOError:
        return last_pos


def find_paths_in_registry():
    ''' Try to find registry entrys for AutoHotkey and Path of Exile '''
    programs = {'AutoHotkey': 'DisplayIcon', 'Steam App 238960': 'InstallLocation', '90A4562F-D4A1-4B65-906D-41F236CF6902': 'InstallSource'}
    paths = {}
    ignore = read_config_part('Registry', 'ignore')

    if ignore != 'yes':
        architec = platform.machine()
        if architec == 'AMD64':
            architec_keys = winreg.KEY_WOW64_64KEY | winreg.KEY_WOW64_32KEY
        else:
            architec_keys = 0

        try:
            regconn = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
            key = winreg.OpenKey(regconn, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall', winreg.KEY_READ | architec_keys)

            for i in range(0, winreg.QueryInfoKey(key)[0]):
                subkey = winreg.EnumKey(key, i)

                if subkey in programs.keys():
                    skey = winreg.OpenKey(key, subkey)

                    try:
                        install_location = winreg.QueryValueEx(skey, programs[subkey])[0]
                        if subkey == 'Steam App 238960' or subkey == '90A4562F-D4A1-4B65-906D-41F236CF6902':
                            paths['POE'] = install_location
                        else:
                            paths[subkey] = install_location
                    except OSError as e:

                        if e.errno == errno.ENOENT:
                            pass
        except (WindowsError, EnvironmentError):
            print('Unable to Connect to the Window Registry and read keys')
        finally:
            key.Close()

    # TODO: check, if POE is installed via steam and normal then use config instead
    if 'AutoHotkey' not in paths.keys():
        autohotkey_path = read_config_part('Paths', 'AutoHotKey')

        if os.path.isfile(autohotkey_path):
            print("Successfully loaded AutoHotKey path from config file")
            paths['AutoHotkey'] = autohotkey_path
        print('AutoHotkey not found in registry')

    if 'POE' not in paths.keys():
        poe_path = read_config_part('Paths', 'poePath')

        if os.path.isfile(os.path.join(poe_path, 'logs', 'Client.txt')):
            print("Successfully loaded poePath from config file")
            paths['POE'] = poe_path

        else:
            print('Could not find Path of Exile in registry. You need to set up the right path manually in the config.ini')
            exit_with_input()

    for key in paths.keys():

        if key == 'AutoHotkey':
            # TODO: just testing
            paths[key] = paths[key][:-4] + 'A32.exe'

        elif key == 'POE':
            paths['POE'] += '\logs\Client.txt'

    return paths


if __name__ == '__main__':
    last_pos = 0
    paths = find_paths_in_registry()

    delete = read_config_part('POE-Log', 'delete')
    if delete.lower() == 'yes':
        delete_poe_log(paths['POE'])

    NEXT_FULL_HOUR = next_full_hour()
    reload_time, file_to_start, play_mp3 = read_config()
    try:
        while True:
            clear()
            end_autohotkey(paths['AutoHotkey'])

            print('[%s] Grabbing new data...' % current_time_str())

            temps_dict = get_current_tempests()
            handle_great_tempests(temps_dict, play_mp3)
            write_to_map_list(temps_dict, file_to_start)

            last_pos = read_poe_log(paths['POE'], last_pos)

            print('[%s] Done. Next try in %d min. Restarting "AutoHotKey"' % (current_time_str(), reload_time))
            subprocess.Popen([paths['AutoHotkey'], file_to_start])
            sleep(reload_time * 60)
    except KeyboardInterrupt:
        end_autohotkey(paths['AutoHotkey'])
