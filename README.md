# TDeskDroid - Telegram Desktop to Android theme converter

## Dependencies
- python 3
- pillow

## Installation
1. Install python 3 for your OS
2. Download or clone this repo to your PC
3. Go to that directory and run `pip install -r requirements.txt` via command prompt / terminal / whatever

## Converting
1. Put .tdesktop-theme file (the one is zip file) to same directory as main.py
2. Run python3 main.py via command prompt / terminal / whatever
3. Go to directory attheme, and send .attheme file to TG chat, then apply it

## About atthemes
- Colors in `.attheme` file is signed int from `ARGB` (yep color alpha goes first)
- Image has to be converted to `jpeg`, and put in binary mode into file between tags PWS and WPE
- `.atthemesrc` is sort of source file made by me so you can check it in more human friendy how conversion goes
- You have to use all the colors in `.tdesktop-theme` file
