import os
import logging
import zipfile
import tarfile
from xml.etree import ElementTree as xml

import pygame

from .errors import WindowError

"""
This module contains style related data classes for the Window Framework 3.0
"""

class Style():

    """
    Style class.
    This class represents the style of the UI. It holds various elements that are used to determine the looks of window objects.
    The purpose of this class is to simplify UI design and separate the visuals from the functionality.

    This class should generally not be initialized, but subclassed instead to provide functionality.
    For a default style object use DefaultStyle.
    Generally it is recommended to subclass from DefaultStyle instead, since it provides compatability with the builtin windows
    in components.py and UI.py
    """

    def __init__(self):

        self.defaultFontSize = 16

        self._fonts = {}
        self._colors = {}
        self._surfs = {}

    def addSurface(self, name, surf):

        """Add a surface to the style using the given name key."""

        if not isinstance(surf, pygame.Surface):
            raise ValueError("surf must be a pygame Surface")
        self._surfs[name] = surf

    def getSurface(self, name, window=None):

        """Get a surface using the given name key and return it. Optional window parameter should be set to the window instance that
        is requesting the surface."""

        return self._surfs[name]

    def addColor(self, name, color):

        """Add a color to the style using the given name key.
        Color can be a sequence or pygame.color.Color"""

        if isinstance(color, list) or isinstance(color, tuple):
            #A color sequence has either 3 (rgb) or 4 (rgba) elements
            if len(color) < 3:
                raise ValueError("Color sequences must have at least three elements")
            if len(color) > 4:
                color = color[:4] #truncate sequence
            self._colors[name] = color

        elif isinstance(color, pygame.color.Color):
            self._colors[name] = (color.r, color.g, color.b, color.a)

        else:
            raise ValueError("color must be a sequence or of type pygame.color.Color")

    def addColour(self, *args, **kwargs):

        """Alias for Style.addColor()"""

        return self.addColor(*args, **kwargs)

    def getColor(self, name, window=None):

        """Get a color using the given name key and return it. Optional window parameter should be set to the window instance that
        is requesting the color.
        The return value will always be a sequence of either 3 or 4 elements."""

        return self._colors[name]

    def getColour(self, *args, **kwargs):

        """Alias for Style.getColor()"""

        return self.getColor(*args, **kwargs)

    def addFont(self, name, font):

        """Add a font to the style using the given name key.
        Font can be of type pygame.font.Font or str, in which case pygame.font.match_font() is used
        to find the corresponding font. The size for font objects created this way will be determined
        by the value of Style.defaultFontSize"""

        if isinstance(font, str):
            font = pygame.font.Font(pygame.font.match_font(font), self.defaultFontSize)

        if not isinstance(font, pygame.font.Font):
            raise ValueError("font must be either str or pygame.font.Font")

        self._fonts[name] = font

    def getFont(self, name, window=None):

        """Get a font using the given name key and return it. Optional window parameter should be set to the window instance that
        is requesting the font."""

        return self._fonts[name]

class DefaultStyle(Style):

    """
    The default style for Window Framework applications.

    This class is used if no style is specified for a project/window.
    It has some special functionality for autoscaling/generating textures and
    also a number of fallbacks in case a resource isn't available.

    Implementors are highly encouraged to subclass this class instead of
    style.Style because of this, since their behaviour should be mostly equivalent,
    with DefaultStyle ensuring that the user doesn't accidentally remove ressources
    needed by the Window Frameworks builtin components.
    """

    def __init__(self):

        Style.__init__(self)

        #defaults
        #the getX methods use these values as a fallback if a certain style element isn't available
        self.defaultFont = pygame.font.Font(None, self.defaultFontSize)
        self.defaultColor = (50, 50, 50)

        #default style
        self.addFont("title", pygame.font.Font(None, 40))
        self.addFont("title2", pygame.font.Font(None, 30))
        self.addFont("title3", pygame.font.Font(None, 20))
        self.addFont("default", self.defaultFont)

        self.addColor("bg", (80, 80, 80))
        self.addColor("bg2", (40, 40, 40))
        self.addColor("hover", (100, 100, 100))
        self.addColor("hover2", (120, 120, 120))
        self.addColor("highlight", (200, 200, 200))
        self.addColor("highlight2", (255, 255, 255))
        self.addColor("error", (255, 0, 0))
        self.addColor("select", (255, 200, 50))
        self.addColor("text", (200, 200, 200))
        self.addColor("text2", (250, 250, 250))

        self.addColor("default", self.defaultColor)

    def getColor(self, name, window = None):
        
        """Get a color using the given name key and return it. Optional window parameter should be set to the window instance that
        is requesting the color.
        The return value will always be a sequence of either 3 or 4 elements."""

        try:
            return Style.getColor(self, name, window)
        except KeyError:
            return self.defaultColor

    def getFont(self, name, window = None):

        """Get a font using the given name key and return it. Optional window parameter should be set to the window instance that
        is requesting the font."""

        try:
            return Style.getFont(self, name, window)
        except KeyError:
            return self.defaultFont

    def _computeHorizontalGradient(self, color1, color2, width, height):

        pass

    def _computeVerticalGradient(self, color1, color2, width, height):

        pass

    def _computePlainSurf(self, color, width, height):

        s = pygame.Surface((width, height))
        s.fill(color)
        return s

    def getSurface(self, name, window = None):
        
        """Get a surface using the given name key and return it. Optional window parameter should be set to the window instance that
        is requesting the surface.
        NOTE: If you are requesting any of the default surface styles, the window argument is mandatory and not explicitly passing it will
        result in a KeyError."""

        try:
            return Style.getSurface(self, name, window)
        except KeyError:
            if window == None:
                raise

        #Now, this is a bit more tricky.
        #we want dynamic surface creation, preferrably gradients for most backgrounds.
        #This is also the reason we didn't define any defaults in the constructor.
        #We use the window instance reference to create a surface that fits the given window in size.

        if name == "bg":
            return self._computePlainSurf(self.getColor("bg"), window.width, window.height)
        elif name == "bg2":
            return self._computePlainSurf(self.getColor("bg2"), window.width, window.height)
        elif name == "buttonBg":
            return self._computeVerticalGradient(self.getColor("bg"), self.getColor("bg2"), window.width, window.height)
        elif name == "buttonBg2" or "buttonBgHover":
            return self._computeVerticalGradient(self.getColor("bg2"), self.getColor("bg"), window.width, window.height)

        return self._computePlainSurf(self.defaultColor, window.width, window.height)

class StylePackageError(WindowError):

    def __init__(self, message="Invalid style package"):

        RuntimeError.__init__(self)
        self.message = message

class StylePackage(DefaultStyle):

    """
    Class for handling file and directory style packages.

    This class provides an interface for designers to create styles without having to deal with the actual
    implementation of the application itself. The programmer loads a "style package", which can be a folder
    or archive file on the disk, that contains all ressources necessary to build the style.
    This makes it possible for a programmer to prototype an application using the builtin defaults and then
    load a style package later to enhance the UI.

    Definition: A collection of ressources describing the looks of a UI element or the entire UI located on
    the filesystem is called a style package, or skin.

    A style package should be located in an arbitrarily named folder or archive. Within the package, the
    following items are REQUIRED:

        - a file named fonts.xml, describing the fonts used by the style.
        - a directory named surfaces, containing the surfaces used by the style.
          The filename should be <name key>.<filename extension>. The name key
          will be used to later reference the item from the application.
          Permitted file types/extensions are all image formats understood by
          pygame.
        - a file named colors.xml, describing the colors used by the style.

    If any of these components are missing from the package, a StylePackageError will be raised.
    If any of these components contain faulty data, a warning will be logged and the respective element will
    be IGNORED. 
    """

    logger = logging.getLogger("StylePackage")

    def __init__(self, path=None):
        
        """
        Create a new StylePackage isntance.
        If path is specified, it must be the path to a valid style package, which
        will be automatically loaded. See StylePackage.loadStylePackage() for more information.
        """

        DefaultStyle.__init__(self)
        if path:
            self.loadStylePackage(path)

    def loadStylePackage(self, path):

        """
        Load a style package located at path.
        This method will figure out how to load the package by itself.
        """

        self.logger.info("Loading style package...")
        if os.path.isdir(path):
            return self._loadDirectory(path)


        elif os.path.isfile(path):
            return self._loadArchive(path)

        #if none of our methods are able to handle the package, raise an error
        self.logger.error("Can't read file at "+path)
        raise StylePackageError("Can't read file at "+path)

    def _loadArchive(self, path):

        if tarfile.is_tarfile(path):
            return self._loadTarArchive(path)
        elif zipfile.is_zipfile(path):
            return self._loadZipArchive(path)

        raise StylePackageError("Can't read file at "+path)

    def _loadTarArchive(self, path):

        try:
            archive = tarfile.open(path)
        except (OSError, IOError, tarfile.TarError) as e:
            self.logger.error("Unable to open archive at "+path+": "+str(e))
            raise

        #check package integrity
        try:
            archive.getmember("fonts.xml")
            archive.getmember("colors.xml")
            archive.getmember("surfaces")
        except KeyError:
            self.logger.error("Archive is missing component(s): "+str(e))
            try:
                archive.close()
            except:
                pass
            raise StylePackageError()

        #load data
        self._loadFonts(archive.extractfile("fonts.xml"))
        self._loadColors(archive.extractfile("colors.xml"))

        #surface file object generator
        def enumerateSurfaces(file):
            members = file.getnames()
            for member in members:
                if os.path.split(member)[0] == "surfaces":
                    yield file.extractfile(member)

        self._loadSurfaces(enumerateSurfaces(archive))
        try:
            archive.close()
        except OSError:
            pass

    def _loadZipArchive(self, path):

        try:
            archive = zipfile.ZipFile(path)
        except (OSError, IOError, zipfile.BadZipFile) as e:
            self.logger.error("Unable to open archive at "+path+": "+str(e))
            raise

        #check package integrity
        try:
            archive.getinfo("fonts.xml")
            archive.getinfo("colors.xml")
            archive.getinfo("surfaces/")
        except KeyError:
            self.logger.error("Archive is missing component(s): "+str(e))
            try:
                archive.close()
            except:
                pass
            raise StylePackageError()

        #load data
        
        self._loadFonts(archive.open("fonts.xml"))
        self._loadColors(archive.open("colors.xml"))

        #surface file object generator
        def enumerateSurfaces(file):
            members = file.namelist()
            for member in members:
                if os.path.split(member)[0] == "surfaces":
                    yield file.open(member)

        self._loadSurfaces(enumerateSurfaces(archive))
        try:
            archive.close()
        except OSError:
            pass

    def _loadDirectory(self, path):

        self.logger.debug("Loading style package located at directory '%s'..." % path)
        if not os.path.isdir(path):
            raise ValueError("The specified directory doesn't exist")

        fontsPath = os.path.join(path, "fonts.xml")
        colorsPath = os.path.join(path, "colors.xml")
        surfPath = os.path.join(path, "surfaces")

        #check package integrity
        if not (os.path.isfile(fontsPath) and os.path.isfile(colorsPath) and os.path.isdir(surfPath)):
            
            logger.error("Package is missing component(s)")
            raise StylePackageError()

        #load data

        with open(fontsPath) as f:
            self._loadFonts(f)
        with open(colorsPath) as f:
            self._loadColors(f)

        #surface file object generator
        def enumerateSurfaces(path):
            files = os.listdir(surfPath)
            for file in files:
                f = open(file)
                yield f
                f.close()

    def _loadFonts(self, file):

        self.logger.info("Loading fonts...")
        doc = xml.parse(file)
        root = doc.getroot()
        for i in root.findall("font"):

            name = i.get("name", None)
            if not name:
                self.logger.error("Font definition has no name identifier, skipping...")
                
            face = i.find("face")
            size = i.find("size")
            if size is not None:
                try:
                    size = int(size.text)
                except:
                    self.logger.error("Invalid integer literal for color '%s'" % name)
                    continue

            if face is not None:
                face = face.text
                if not os.path.isfile(face):
                    #if the font isn't specified as a file path
                    #we assume it is a system font so pygame should be
                    #able to find it...
                    face = pygame.font.match_font(face)
                    if face == None:
                        self.logger.warn("Unable to find source file for font '%s'" % name)
            
            if not size:
                size = self.defaultFontSize
            self.addFont(name, pygame.font.Font(face, size))

    def _loadSurfaces(self, gen):

        pass

    def _loadColors(self, file):

        self.logger.info("Loading colors...")
        doc = xml.parse(file)
        root = doc.getroot()
        for i in root.findall("color"):
            
            name = i.get("name", None)
            if not name:
                self.logger.error("Color definition has no name identifier, skipping...")

            color = i.find("value")
            if color is None:
                continue

            color = color.text
            
            if color.startswith("#"):
                #try to read color in hex format
                try:
                    v = int(color[1:], 16)
                except ValueError:
                    self.logger.error("Invalid color literal for color '%s'" % name)
                    continue

                color = (v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF)
                self.addColor(name, color)
                continue

            l = color.split(",")
            if len(l) == 3:
                try:
                    color = tuple(map(int, l))
                except ValueError:
                    self.logger.error("Invalid color literal for color '%s'" % name)
                    continue
                self.addColor(name, color)
                continue

            try:
                v = int(color)
            except ValueError:
                self.logger.error("Invalid color literal for color '%s'" % name)
                continue
            
            color = (v >> 16 & 0xFF, v >> 8 & 0xFF, v & 0xFF)
            self.addColor(name, color)
