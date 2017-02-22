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
    return '{:02x}{:02x}{:02x}'.format(r, g, b)

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

def makeAtthemeSrc(filename, hasBg):
    src = open("./wip/" + filename + "/colors.tdesktop-theme", "r")
    thememap = open("theme.map", "r")
    themesrc = open("./wip/atthemesrc/" + filename + ".atthemesrc", "w")

    rulelist = []
    srcrules = []
    bgColor = ""

    for line in thememap:
        rule = line.strip().split("=")
        rulelist.append([rule[1],rule[0]])

    for line in src:
        strippedline = line.strip()
        if strippedline.startswith("/") or strippedline.startswith("*") or len(strippedline) < 1:
            pass
        else:
            rule = strippedline.split(":")
            rulename = rule[0].strip()
            potcolor = rule[1].split("//")[0].strip()
            if rulename == "convChatBackgroundColor":
                hasBg = True
            if potcolor.startswith("#"):
                if len(potcolor[1:-1]) == 8:
                    color = potcolor[1:-1]
                else:
                    color = potcolor[1:-1] + "ff"
            else :
                for srcrule in srcrules:
                    if srcrule[0] == potcolor[:-1]:
                        color = srcrule[1]
            srcrules.append([rulename,color])

    srcrules.append(["whatever", "ff00ffff"])
    srcrules.append(["findme", "00ffffff"])

    if hasBg == False:
        srcrules.append(["convChatBackgroundColor", getBgColor(filename)+"ff"])

    for themerule in srcrules:
        for maprule in rulelist:
            if maprule[0] == themerule[0]:
                themesrc.write(maprule[1]+"=#"+themerule[1]+"\n")

    src.close()
    thememap.close()
    themesrc.close()

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
        img = open("./wip/" + filename + "/optimised.jpg", "rb")
        theme.write(img.read())
        theme.close()
        theme = open("./attheme/" + filename + ".attheme", "a")
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

print ("""Convetring done.\n
If you have any bugs feel free to contact me:
https://t.me/TDeskDroid
https://github.com/MrYadro/TDeskDroid/issues/new""")
