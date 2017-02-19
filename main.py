from PIL import Image
import os
import zipfile

def convertFromSignedHex(s):
    x = int(s,16)
    if x > 0x7FFFFFFF:
        x -= 0x100000000
    return x

def getbgcolor(path):
    filenames = ["background", "tiled"]
    filetypes = ["jpg", "png"]
    size = 1,1
    tries = 0

    for filename in filenames:
        for filetype in filetypes:
            try:
                im = Image.open(path + "/" + filename + "." + filetype)
            except FileNotFoundError:
                tries += 1
                pass

    if tries == 4:
        return "ff00ff"

    rgb_im = im.convert('RGB')
    im.thumbnail(size, Image.ANTIALIAS)
    r, g, b = rgb_im.getpixel((1, 1))
    return '{:02x}{:02x}{:02x}'.format(r, g, b)

def makeAtthemeSrc(filename):
    src = open(filename + "/colors.tdesktop-theme", "r")
    thememap = open("theme.map", "r")
    themesrc = open("./tthemesrc/" + filename + ".atthemesrc", "w")

    rulelist = []
    srcrules = []
    bg = False
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
            if rulename == "convChatBackgroundColor":
                bg = True
            potcolor = rule[1].split("//")[0].strip()
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

    if bg == False:
        srcrules.append(["convChatBackgroundColor", getbgcolor(filename)+"ff"])

    for themerule in srcrules:
        for maprule in rulelist:
            if maprule[0] == themerule[0]:
                themesrc.write(maprule[1]+"=#"+themerule[1]+"\n")

    src.close()
    thememap.close()
    themesrc.close()

def makeAttheme(filename):
    src = open("./tthemesrc/" + filename + ".atthemesrc", "r")
    theme = open("./ttheme/" + filename + ".attheme", "w")

    for line in src:
        magicColor = line.strip().split("=")
        if magicColor[0] == "switchTrack" or magicColor[0] == "switchTrackChecked":
            swapedColor = "88"+magicColor[1][1:7]
        elif magicColor[0] == "chat_selectedBackground":
            swapedColor = "66"+magicColor[1][1:7]
        elif magicColor[0] == "chat_messagePanelVoiceShadow":
            swapedColor = "D0"+magicColor[1][1:7]
        elif magicColor[0] == "contextProgressInner1" or magicColor[0] == "contextProgressInner2":
            swapedColor = "41"+magicColor[1][1:7]
        elif magicColor[0] == "chats_menuPhone" or magicColor[0] == "chats_menuPhoneCats":
            swapedColor = "99"+magicColor[1][1:7]
        else:
            swapedColor = magicColor[1][-2:]+magicColor[1][1:7]
        i = convertFromSignedHex(swapedColor)
        theme.write(magicColor[0]+"="+str(i)+"\n")

    src.close()
    theme.close()

for directory in ["tthemesrc", "ttheme"]:
    if not os.path.exists(directory):
        os.makedirs(directory)

for file in os.listdir("./"):
    if file.endswith(".tdesktop-theme"):
        filename = file[:-15]
        with zipfile.ZipFile(file,"r") as zip_ref:
            zip_ref.extractall(filename)
            makeAtthemeSrc(filename)
            makeAttheme(filename)
