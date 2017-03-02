from PIL import Image
import os
import zipfile
import os.path
import requests

DESKTOP_DIR          = 'desktop'
ANDROID_DIR          = 'android'
WIP_DIR              = 'wip'
MAPS_DIR             = 'maps'
WIP_DROIDSRC_DIR     = os.path.join(WIP_DIR, 'atthemesrc')
DESKTOP_EXT          = '.tdesktop-theme'
ANDROID_EXT          = '.attheme'
JPEG_NAME            = 'converted.jpg'
THEME_MAP_PATH       = os.path.join(MAPS_DIR, 'theme.map')
THEME_MAP_URL        = 'https://raw.githubusercontent.com/TThemes/TThemeMap/master/desktop_android.map'
THEME_ALPHA_MAP_PATH = os.path.join(MAPS_DIR, 'theme_alpha.map')
THEME_ALPHA_MAP_URL  = 'https://raw.githubusercontent.com/TThemes/TThemeMap/master/desktop_android_trans.map'
THEME_DEFAULT_PATH   = os.path.join(MAPS_DIR, 'default.map')
THEME_DEFAULT_URL    = 'https://raw.githubusercontent.com/telegramdesktop/tdesktop/master/Telegram/Resources/colors.palette'
OVERRIDE_MAP_PATH    = os.path.join(MAPS_DIR, 'override.map')
TINIFY_KEY           = 'API_KEY_HERE'
TINIFY_ENABLE        = False


class TDeskDroid(object):
    _defaultThemeMap = None

    def _checkDirectories(self):
        for directory in [DESKTOP_DIR, ANDROID_DIR, WIP_DIR, WIP_DROIDSRC_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def _updateThemesMap(self):
        print("Downloading [desktop => android] mapping")
        themesMapContents = requests.get(THEME_MAP_URL)
        with open(THEME_MAP_PATH, 'w') as themeMap:
            themeMap.write(themesMapContents.text)
        print("Downloading transparency fixups")
        themesMapContents = requests.get(THEME_ALPHA_MAP_URL)
        with open(THEME_ALPHA_MAP_PATH, 'w') as themeMap:
            themeMap.write(themesMapContents.text)
        print("Downloading default desktop theme")
        themesMapContents = requests.get(THEME_DEFAULT_URL)
        with open(THEME_DEFAULT_PATH, 'w') as themeMap:
            themeMap.write(themesMapContents.text)

    def tinifyJpeg(self, jpegPath):
        import tinify
        tinify.key = TINIFY_KEY
        source = tinify.from_file(jpegPath)
        source.to_file(jpegPath)

    def _convertBackround(self, path, tinyJpeg):
        filename = "background"
        filetypes = ["jpg", "png"]
        success = False
        image = None
        for filetype in filetypes:
            try:
                image = Image.open(os.path.join(WIP_DIR, path, filename + "." + filetype))
                success = True
            except FileNotFoundError:
                pass
        if not success or not image:
            print ('Warning: failed to convert background')
            return False
        jpegPath = os.path.join(WIP_DIR, path, JPEG_NAME)
        image.save(jpegPath, "jpeg", quality=100)
        if tinyJpeg:
            self.tinifyJpeg(jpegPath)
        return True

    def _normalizeColor(self, color):
        color = color.lower()
        if len(color) < 9:
            color += "ff"
        return color

    def _substituteColor(self, rulesDict, color):
        if color.startswith("#"):
            return self._normalizeColor(color)
        return self._substituteColor(rulesDict, rulesDict[color])

    def _validateKeyValue(self, line, divider='='):
        return (
            line
            and len(line) > 0
            and divider in line
            and (
                line[0].isalpha() or line[0] == '_'
            )
        )

    def _getKeyValue(self, line, divider='=', spliter='//'):
        key, value = line.split(divider, 1)
        key = key.strip()
        value = value.split(spliter, 1)[0].strip()
        return key, value

    def _applyOverrideMap(self, overrideMapPath):
        overrideDict = {}
        if not os.path.exists(overrideMapPath):
            return overrideDict
        print("Applying '{}' override map".format(os.path.basename(overrideMapPath)))
        with open(overrideMapPath, "r") as overrideMap:
            for line in overrideMap:
                if not self._validateKeyValue(line):
                    continue
                name, color = self._getKeyValue(line)
                if color.startswith("#"):
                    color = self._normalizeColor(color)
                overrideDict[name] = color
        return overrideDict

    @property
    def defaultThemeMap(self):
        if self._defaultThemeMap is None:
            self._defaultThemeMap = {}
            themeDefault = open(THEME_DEFAULT_PATH, "r").readlines()
            for line in themeDefault:
                if not self._validateKeyValue(line, ':'):
                    continue
                name, color = self._getKeyValue(line, ':', ';')
                self._defaultThemeMap[name] = color
        return self._defaultThemeMap

    def _makeAtthemeSrc(self, filedir, filename):
        src = open(os.path.join(WIP_DIR, filename, "colors.tdesktop-theme"), "r").readlines()
        themeMap = open(THEME_MAP_PATH, "r").readlines()
        themeAlphaMap = open(THEME_ALPHA_MAP_PATH, "r").readlines()

        # read original theme file
        srcrules = {}
        for line in src:
            if not self._validateKeyValue(line, ':'):
                continue
            name, color = self._getKeyValue(line, ':', ';')
            srcrules[name] = color

        overrideMap = self._applyOverrideMap(OVERRIDE_MAP_PATH)
        srcrules.update(overrideMap)

        # substitute color values
        for rule, color in srcrules.items():
            srcrules[rule] = self._substituteColor(srcrules, color)

        # parse theme.map
        destrules = {}
        for line in themeMap:
            if not self._validateKeyValue(line):
                continue
            name, color = self._getKeyValue(line)
            while True:
                try:
                    destrules[name] = self._substituteColor(srcrules, color)
                    break
                except KeyError:
                    try:
                        color = self.defaultThemeMap[color]
                    except KeyError:
                        print("Warning: couldn't find '{}' value. Using default color for '{}'.".format(color, name))

        for line in themeAlphaMap:
            if not self._validateKeyValue(line):
                continue
            name, alpha = self._getKeyValue(line)
            color = destrules[name]
            destrules[name] = color[:7] + alpha

        # apply overrides from map files
        destrules.update(overrideMap)
        overrideMapPath = filedir + os.path.sep
        for filepart in os.path.basename(filename).split("."):
            overrideMapPath += filepart + "."
            overrideMap = self._applyOverrideMap(overrideMapPath + "map")
            destrules.update(overrideMap)

        # substitute color values for overrides
        for rule, color in destrules.items():
            destrules[rule] = self._substituteColor(destrules, color)

        # write theme file
        with open(os.path.join(WIP_DROIDSRC_DIR, filename + ".atthemesrc"), "w") as themesrc:
            for rule, color in destrules.items():
                themesrc.write(rule + "=" + color + "\n")

    def _generateCredits(self):
        return (
            "If you have any bugs feel free to contact:\n"
            "https://t.me/TThemesHQ\n"
            "https://github.com/MrYadro/TDeskDroid/issues/new\n"
        )

    def _makeAttheme(self, filename, hasBg):
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

    def convert(self):
        self._checkDirectories()
        self._updateThemesMap()
        filedir = DESKTOP_DIR
        for file in os.listdir(filedir):
            if file.endswith(DESKTOP_EXT):
                filename = os.path.splitext(file)[0]
                with zipfile.ZipFile(os.path.join(DESKTOP_DIR, file),"r") as zip_ref:
                    print ("> Converting '" + filename + "'")
                    zip_ref.extractall(os.path.join(WIP_DIR, filename))
                    hasBg = self._convertBackround(filename, TINIFY_ENABLE)
                    self._makeAtthemeSrc(filedir, filename)
                    self._makeAttheme(filename, hasBg)
        print ("> Converton done\n")
        print ('-' * 30)
        print (self._generateCredits())

TDeskDroid().convert()
