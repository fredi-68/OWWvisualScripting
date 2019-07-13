import enum

class SDLFlags(enum.Enum):

    CENTER_WINDOW = "SDL_VIDEO_CENTERED"
    WINDOW_POS = "SDL_VIDEO_WINDOW_POS"
    VIDEO_DRIVER = "SDL_VIDEODRIVER"
    WINDOW_ID = "SDL_WINDOW_ID"
    X11_WMCLASS = "SDL_VIDEO_X11_WMCLASS"

class SDLDrivers(enum.Enum):

    DIRECTX = "directx"
    WINDIB = "windib"
    X11 = "x11"
    DGA = "dga"
    FBCON = "fbcon"
    DIRECTFB = "directfb"
    GGI = "ggi"
    VGL = "vgl"
    SVGALIB = "svgalib"
    AALIB = "aalib"
