![asd](http://i.imgur.com/ajf4S5e.png?1)

# poe_tempest_iteminfo
Updates ItemInfo with the newest tempest zone-mods from __http://poetempest.com__

## Features
- Grabs data from __http://poetempest.com__ developed by Justin Vanderheide
- Writes it back to MapList.txt that it can be accessed ingame via ItemInfo
- Makes a sound, if a good tempest is reported
- Report new tempests ingame over chat that will be registered on the webpage

## Report function
Write `TEMPEST: <MAP>, <Temest Name>` ingame in chat.
For example `TEMPEST: Tropical Island, Morbid Tempest of Precision`
or if there is no active tempest on the map: `TEMPEST: Tropical Island, None`

## Installation
If you do not have Python installed you can download an executable from [here](https://github.com/shlnz/poe_tempest_iteminfo/releases)

1. Download and install AutoHotKey from " http://ahkscript.org"
2. Download ItemInfo from "https://sites.google.com/site/poeiteminfoscript/"
   and extract the file to a location, e.g. "C:\PoE-Item-Info"
3. Extract the poe_tempest_iteminfo-0.x.zip
4. Adjust the "config.ini" file. You may need to set the path to AutoHotKey.exe and Path of Exile, if it can't be found in the registry. Set the path to ItemInfo Script that you want to start.
5. Run "poe_tempest.exe"

## Upcoming
- Fixing Bugs
- Improvements
- Add function to ItemInfo to display good tempests ingame
