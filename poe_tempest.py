import urllib.request
import os
import sys
import configparser
import psutil
import subprocess
from time import sleep
from datetime import datetime
from bs4 import BeautifulSoup


def current_time():
    return datetime.now().strftime('%H:%M:%S')


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

        try:
            approot = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            approot = os.path.dirname(os.path.abspath(sys.argv[0]))

        with open(os.path.abspath(os.path.join(approot, '..', 'data', 'MapList.txt')), 'w') as f:
            f.write(new_file)

    except IOError:
        print('[%s] ERROR: Could not find file "MapList.txt"' % current_time())
        sys.exit(1)


def get_sourcepage(url):
    successful = False
    while not successful:
        try:
            page = urllib.request.urlopen(url).read()
            page = str(page, 'utf-8')
            soup = BeautifulSoup(''.join(page), 'html.parser')
            successful = True
        except urllib.error.URLError as e:
            print('[%s] %s' % e.reason)
            sleep(2)
    return soup


def find_table_content(soup):
    table = soup.find('tbody')
    row = table.find_all('tr')
    table_content = []
    for elemtents in row:
        table_content.append(elemtents.getText().strip().split('\n'))
    return table_content


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        auto_hot_key = config['Path']['AutoHotKey']
        file_to_start = config['Path']['ItemInfo']
        reaload = int(config['RefreshInterval']['reaload'])
    except KeyError:
        print("You need to adjust the config.ini")
        sleep(5)
        sys.exit()

    return auto_hot_key, reaload, file_to_start


def end_autohotkey(prog_path):
    procname = prog_path.split('\\')[-1]

    for proc in psutil.process_iter():
        if proc.name() == procname:
            proc.kill()


if __name__ == '__main__':
    prog_path, reload_time, file_to_start = read_config()
    try:
        while True:
            end_autohotkey(prog_path)
            print('[%s] Grabbing new data...' % current_time())
            url = 'http://poetempest.com/'
            soup = get_sourcepage(url)
            table_content = find_table_content(soup)
            write_to_map_list(table_content)
            print('[%s] Done. Next try in %d min. Restarting "AutoHotKey"' % (current_time(), reload_time))
            subprocess.Popen([prog_path, file_to_start])
            sleep(reload_time * 60)
    except KeyboardInterrupt:
        end_autohotkey(prog_path)
        sys.exit(1)
