from PIL import Image
import os
import zipfile
import os.path
import requests

DESKTOP_DIR          = 'desktop'
ANDROID_DIR          = 'android'
WIP_DIR              = 'wip'
WIP_DROIDSRC_DIR     = os.path.join(WIP_DIR, 'atthemesrc')
DESKTOP_EXT          = '.tdesktop-theme'
ANDROID_EXT          = '.attheme'
JPEG_NAME            = 'converted.jpg'
THEME_MAP_PATH       = 'theme.map'
THEME_MAP_URL        = 'https://raw.githubusercontent.com/TThemes/TThemeMap/master/desktop_android.map'
THEME_ALPHA_MAP_PATH = 'theme_alpha.map'
THEME_ALPHA_MAP_URL  = 'https://raw.githubusercontent.com/TThemes/TThemeMap/master/desktop_android_trans.map'
OVERRIDE_MAP_PATH    = 'override.map'
TINIFY_KEY           = "API_KEY_HERE"
TINIFY_ENABLE        = False



def checkDirectories():
    for directory in [DESKTOP_DIR, ANDROID_DIR, WIP_DIR, WIP_DROIDSRC_DIR]:
        if not os.path.exists(directory):
            os.makedirs(directory)

def updateThemesMap():
    print("Downloading '" + THEME_MAP_PATH + "'")
    themesMapContents = requests.get(THEME_MAP_URL)
    with open(THEME_MAP_PATH, 'w') as themeMap:
        themeMap.write(themesMapContents.text)
    print("Downloading '" + THEME_ALPHA_MAP_PATH + "'")
    themesMapContents = requests.get(THEME_ALPHA_MAP_URL)
    with open(THEME_ALPHA_MAP_PATH, 'w') as themeAlphaMap:
        themeAlphaMap.write(themesMapContents.text)

def convertBackround(path, tinyJpeg):
    filename = "background"
    filetypes = ["jpg", "png"]
    tries = 0

    for filetype in filetypes:
        try:
            im = Image.open(os.path.join(WIP_DIR, path, filename + "." + filetype))
        except FileNotFoundError:
            tries += 1
            pass

    if tries == 2:
        return False

    jpg_path = os.path.join(WIP_DIR, path, JPEG_NAME)
    im.save(jpg_path, "jpeg", quality=100)
    if tinyJpeg:
        import tinify
        tinify.key = TINIFY_KEY
        source = tinify.from_file(jpg_path)
        source.to_file(jpg_path)
    return True

def normalizeColor(color):
    color = color.lower()
    if len(color) < 9:
        color += "ff"
    return color

def substituteColor(rulesDict, color):
    if color.startswith("#"):
        return normalizeColor(color)
    return substituteColor(rulesDict, rulesDict[color])

def validateKeyValue(line, divider='='):
    return (
        line
        and len(line) > 0
        and divider in line
        and (
            line[0].isalpha() or line[0] == '_'
        )
    )

def getKeyValue(line, divider='=', spliter='//'):
    key, value = line.split(divider, 1)
    key = key.strip()
    value = value.split(spliter, 1)[0].strip()
    return key, value

def applyOverrideMap(overrideMapPath):
    overrideDict = {}
    if not os.path.exists(overrideMapPath):
        return overrideDict
    print("Applying '{}' override map".format(overrideMapPath))
    with open(overrideMapPath, "r") as overrideMap:
        for line in overrideMap:
            if not validateKeyValue(line):
                continue
            name, color = getKeyValue(line)
            if color.startswith("#"):
                color = normalizeColor(color)
            overrideDict[name] = color
    return overrideDict

def makeAtthemeSrc(filedir, filename):
    src = open(os.path.join(WIP_DIR, filename, "colors.tdesktop-theme"), "r").readlines()
    themeMap = open(THEME_MAP_PATH, "r").readlines()
    themeAlphaMap = open(THEME_ALPHA_MAP_PATH, "r").readlines()

    # read original theme file
    srcrules = {}
    for line in src:
        if not validateKeyValue(line, ':'):
            continue
        name, color = getKeyValue(line, ':', ';')
        srcrules[name] = color

    overrideMap = applyOverrideMap(OVERRIDE_MAP_PATH)
    srcrules.update(overrideMap)

    # substitute color values
    for rule, color in srcrules.items():
        srcrules[rule] = substituteColor(srcrules, color)

    # parse theme.map
    destrules = dict()
    for line in themeMap:
        if not validateKeyValue(line):
            continue
        name, color = getKeyValue(line)
        try:
            destrules[name] = substituteColor(srcrules, color)
        except KeyError:
            print("Warning: couldn't find '{}' value. Using default color for '{}'.".format(color, name))

    for line in themeAlphaMap:
        if not validateKeyValue(line):
            continue
        name, alpha = getKeyValue(line)
        color = destrules[name]
        destrules[name] = color[:7] + alpha

    # apply overrides from map files
    destrules.update(overrideMap)
    overrideMapPath = filedir + os.path.sep
    for filepart in os.path.basename(filename).split("."):
        overrideMapPath += filepart + "."
        overrideMap = applyOverrideMap(overrideMapPath + "map")
        destrules.update(overrideMap)

    # substitute color values for overrides
    for rule, color in destrules.items():
        destrules[rule] = substituteColor(destrules, color)

    # write theme file
    with open(os.path.join(WIP_DROIDSRC_DIR, filename + ".atthemesrc"), "w") as themesrc:
        for rule, color in destrules.items():
            themesrc.write(rule + "=" + color + "\n")

def makeAttheme(filename, hasBg):
    src = open(os.path.join(WIP_DROIDSRC_DIR, filename + ".atthemesrc"), "r").readlines()
    with open(os.path.join(ANDROID_DIR, filename + ANDROID_EXT), "wb") as theme:
        for line in src:
            name, color = line.strip().split("=")
            swappedColor = color[-2:] + color[1:7]
            theme.write((name + "=#" + swappedColor + "\n").encode())

        if hasBg:
            theme.write("WPS\n".encode())
            img = open(os.path.join(WIP_DIR, filename, JPEG_NAME), "rb")
            theme.write(img.read())
            theme.write("\nWPE".encode())

checkDirectories()
updateThemesMap()

filedir = DESKTOP_DIR
for file in os.listdir(filedir):
    if file.endswith(DESKTOP_EXT):
        filepath = os.path.join(filedir, file)
        filename = os.path.splitext(file)[0]
        with zipfile.ZipFile(os.path.join(DESKTOP_DIR, file),"r") as zip_ref:
            print ("Converting '" + filename + "'")
            zip_ref.extractall(os.path.join(WIP_DIR, filename))
            hasBg = convertBackround(filename, TINIFY_ENABLE)
            makeAtthemeSrc(filedir, filename)
            makeAttheme(filename, hasBg)

print ("""Converton done\n
If you have any bugs feel free to contact me:
https://t.me/TDeskDroid
https://github.com/MrYadro/TDeskDroid/issues/new""")
