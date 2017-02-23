from PIL import Image
import os
import zipfile
import os.path
import tinify

def convertFromSignedHex(s):
    x = int(s,16)
    if x > 0x7FFFFFFF:
        x -= 0x100000000
    return x

def getBgColor(path):
    filename = "tiled"
    filetypes = ["jpg", "png"]
    size = 1,1
    tries = 0

    for filetype in filetypes:
        try:
            im = Image.open("./wip/" + path + "/" + filename + "." + filetype)
        except FileNotFoundError:
            tries += 1
            pass

    if tries == 2:
        return "ff00ff"

    rgb_im = im.convert('RGB')
    im.resize(size, Image.ANTIALIAS)
    r, g, b = rgb_im.getpixel((0, 0))
    return '#{:02x}{:02x}{:02x}ff'.format(r, g, b)

def convertBackround(path, tinyJpeg):
    filename = "background"
    filetypes = ["jpg", "png"]
    tries = 0

    for filetype in filetypes:
        try:
            im = Image.open("./wip/" + path + "/" + filename + "." + filetype)
        except FileNotFoundError:
            tries += 1
            pass

    if tries == 2:
        return False

    im.save("./wip/" + path + "/converted.jpg", "jpeg", quality=100)
    if tinyJpeg:
        source = tinify.from_file("./wip/" + path + "/converted.jpg")
        source.to_file("./wip/" + path + "/converted.jpg")
    return True

def readOverrideMap(overrideMapPath):
    overrideDict = {}
    if not os.path.exists(overrideMapPath):
        return overrideDict
    print("Applying '{}' override map".format(overrideMapPath))
    with open(overrideMapPath, "r") as overrideMap:
        for line in overrideMap:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            overrideDict[key] = value
    return overrideDict

def makeAtthemeSrc(filename, hasBg):
    with open("./wip/" + filename + "/colors.tdesktop-theme", "r") as src:
        with open("theme.map", "r") as thememap:
            with open("./wip/atthemesrc/" + filename + ".atthemesrc", "w") as themesrc:
                # read original theme file
                srcrules = {}
                for line in src:
                    strippedline = line.strip()
                    if strippedline.startswith("/") or strippedline.startswith("*") or len(strippedline) < 1:
                        continue
                    key, value = strippedline.split(":", 1)
                    key = key.strip()
                    value = value.split(";")[0].strip()
                    if key == "convChatBackgroundColor":
                        hasBg = True
                    if value.startswith("#") and len(value) < 9:
                        value += "ff"
                    srcrules[key] = value

                # add default values and fixups
                srcrules["whatever"] = "#ff00ffff"
                srcrules["findme"] = "#00ffffff"
                if hasBg == False:
                    srcrules["convChatBackgroundColor"] = getBgColor(filename)

                # substitute color values
                for rule, color in srcrules.items():
                    if color.startswith("#"):
                        continue
                    srcrules[rule] = srcrules[color]

                # parse theme.map
                destrules = dict()
                for line in thememap:
                    droid, desk = line.strip().split("=")
                    try:
                        destrules[droid] = srcrules[desk].lower()
                    except KeyError:
                        print("Warning: couldn't find '{}' value. Using white color for '{}'.".format(desk, droid))
                        destrules[droid] = "#ffffffff"

                # apply overrides from map files
                overrideMapPath = os.path.dirname(filename)
                for filepart in os.path.basename(filename).split("."):
                    overrideMapPath += filepart + "."
                    overrideMap = readOverrideMap(overrideMapPath + "map")
                    destrules.update(overrideMap)

                # write theme file
                for rule, color in destrules.items():
                    themesrc.write(rule + "=" + color + "\n")

def makeAttheme(filename, hasBg):
    src = open("./wip/atthemesrc/" + filename + ".atthemesrc", "r")
    theme = open("./attheme/" + filename + ".attheme", "w")

    for line in src:
        magicColor = line.strip().split("=")
        if magicColor[0] == "switchTrack" or magicColor[0] == "switchTrackChecked" or magicColor[0] == "dialogLinkSelection" or magicColor[0] == "picker_disabledButton":
            swapedColor = "88"+magicColor[1][1:7]
        elif magicColor[0] == "chat_selectedBackground":
            swapedColor = "66"+magicColor[1][1:7]
        elif magicColor[0] == "chat_messagePanelVoiceShadow":
            swapedColor = "D0"+magicColor[1][1:7]
        elif magicColor[0] == "contextProgressInner1" or magicColor[0] == "contextProgressInner2":
            swapedColor = "41"+magicColor[1][1:7]
        elif magicColor[0] == "chats_menuPhone" or magicColor[0] == "chats_menuPhoneCats":
            swapedColor = "99"+magicColor[1][1:7]
        elif magicColor[0] == "chats_tabletSelectedOverlay":
            swapedColor = "77"+magicColor[1][1:7]
        else:
            swapedColor = magicColor[1][-2:]+magicColor[1][1:7]
        i = convertFromSignedHex(swapedColor)
        theme.write(magicColor[0]+"="+str(i)+"\n")

    if hasBg == True:
        theme.write("WPS\n")
        theme.close()
        theme = open("./attheme/" + filename + ".attheme", "ab")
        img = open("./wip/" + filename + "/converted.jpg", "rb")
        theme.write(img.read())
        theme.close()
        theme = open("./attheme/" + filename + ".attheme", "a")
        theme.write("\nWPE")
        theme.write("\nWPE")

    src.close()
    theme.close()

tinify.key = "API_KEY_HERE"

tinyJpeg = False

for directory in ["wip", "wip/atthemesrc", "attheme"]:
    if not os.path.exists(directory):
        os.makedirs(directory)

for file in os.listdir("./"):
    if file.endswith(".tdesktop-theme"):
        filename = file[:-15]
        with zipfile.ZipFile(file,"r") as zip_ref:
            print ("Converting " + filename)
            zip_ref.extractall("./wip/" + filename)
            hasBg = convertBackround(filename, tinyJpeg)
            makeAtthemeSrc(filename, hasBg)
            makeAttheme(filename, hasBg)

print ("""Converting done.\n
If you have any bugs feel free to contact me:
https://t.me/TDeskDroid
https://github.com/MrYadro/TDeskDroid/issues/new""")
