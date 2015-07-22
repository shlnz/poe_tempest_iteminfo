import urllib.request
import os
import sys
import configparser
import psutil
import subprocess
import winsound
from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup

clear = lambda: os.system("cls")


def exit_with_input():
    input("Exit with any key")
    sys.exit()


def current_time():
    return datetime.now().strftime('%H:%M:%S')


def dummy_html():
    with open('quellcode.html', 'r') as f:
        return BeautifulSoup(''.join(f), 'html.parser')


def write_to_map_list(table_content):
    try:
        new_file = ''
        with open('MapList.txt', 'r') as f:
            for line in f:
                for row in table_content:
                    map_name = row[0][:-5] + ' Map'
                    if line.startswith('mapList["' + map_name):
                        line = line[:-2] + '`n`nTempest on map:`n- ' + row[1] + '`n- ' + row[2] + '"\n'
                new_file += line
    except IOError:
        print('[%s] ERROR: Could not find file "MapList.txt" in script folder.' % current_time())
        exit_with_input()

    try:
        approot = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        approot = os.path.dirname(os.path.abspath(sys.argv[0]))

    try:
        with open(os.path.abspath(os.path.join(approot, '..', 'data', 'MapList.txt')), 'w') as f:
            f.write(new_file)
    except IOError:
        print('[%s] ERROR: Could not find file "MapList.txt" in data folder. Maybe you placed this script into the wrong location.' % current_time())
        exit_with_input()


def get_sourcepage(url):
    successful = False
    while not successful:
        try:
            page = urllib.request.urlopen(url).read()
            page = str(page, 'utf-8')
            soup = BeautifulSoup(''.join(page), 'html.parser')
            successful = True
        except urllib.error.URLError as e:
            print('[%s] %s' % (current_time(), e.reason))
            sleep(2)
    return soup


def play_sound():
    fname = 'beep.wav'
    winsound.PlaySound(fname, winsound.SND_FILENAME)


def show_tempest_info(great):
    print('')
    print('[%s] Good tempests:' % current_time())
    print('------------------------------------')
    for items in great:
        tlist = items.getText().strip().split('\n')
        tlist = [i.strip() for i in tlist if i.strip() and i.strip() not in ['thumb_up', 'thumb_down']]
        print('[%s] Map:          %s' % (current_time(), tlist[0]))
        print('[%s] Votes:        %s' % (current_time(), tlist[1]))
        print('[%s] Tempest:      %s' % (current_time(), tlist[2]))
        print('[%s] Description:  %s' % (current_time(), tlist[3]))
        print('------------------------------------')


def find_table_content(soup, play_mp3):
    table = soup.find('tbody')
    row = table.find_all('tr', {'class': ['', 'great', 'dangerous']})
    great = table.find_all('tr', {'class': 'great'})

    if great:
        show_tempest_info(great)
        if play_mp3.lower() == 'true':
            play_sound()

    table_content = []
    for elemtents in row:
        tlist = elemtents.getText().strip().split('\n')
        tlist = [i.strip() for i in tlist if i.strip() and i.strip() not in ['thumb_up', 'thumb_down']]

        if len(tlist) == 4:
            del tlist[1]
        table_content.append(tlist)

    return table_content


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        auto_hot_key = config['Path']['AutoHotKey']
        file_to_start = config['Path']['ItemInfo']
        reaload = int(config['RefreshInterval']['reaload'])
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

    return auto_hot_key, reaload, file_to_start, play_mp3


def end_autohotkey(prog_path):
    procname = prog_path.split('\\')[-1]

    for proc in psutil.process_iter():
        if proc.name() == procname:
            proc.kill()


if __name__ == '__main__':
    # TODO: READ LOGFILE FROM POE
    prog_path, reload_time, file_to_start, play_mp3 = read_config()
    try:
        while True:
            clear()
            end_autohotkey(prog_path)
            print('[%s] Grabbing new data...' % current_time())
            url = 'http://poetempest.com/'
            soup = get_sourcepage(url)
            #soup = dummy_html()
            table_content = find_table_content(soup, play_mp3)
            write_to_map_list(table_content)
            print('[%s] Done. Next try in %d min. Restarting "AutoHotKey"' % (current_time(), reload_time))
            subprocess.Popen([prog_path, file_to_start])
            sleep(reload_time * 60)
    except KeyboardInterrupt:
        end_autohotkey(prog_path)
