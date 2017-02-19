from PIL import Image

filenames = ["colors"]

def getbgcolor():
    filenames = ["background", "tiled"]
    filetypes = ["png", "jpg"]
    size = 1,1

    for filename in filenames:
        for filetype in filetypes:
            try:
                im = Image.open(filename + "." + filetype)
            except FileNotFoundError:
                pass

    rgb_im = im.convert('RGB')
    im.thumbnail(size, Image.ANTIALIAS)
    r, g, b = rgb_im.getpixel((1, 1))
    return '{:02x}{:02x}{:02x}'.format(r, g, b)

for filename in filenames:
    src = open(filename + ".tdesktop-theme", "r")
    thememap = open("theme.map", "r")
    themesrc = open(filename + ".atthemesrc", "w")

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
            print("skip")
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
        srcrules.append(["convChatBackgroundColor", getbgcolor()+"ff"])

    for themerule in srcrules:
        for maprule in rulelist:
            if maprule[0] == themerule[0]:
                themesrc.write(maprule[1]+"=#"+themerule[1]+"\n")
