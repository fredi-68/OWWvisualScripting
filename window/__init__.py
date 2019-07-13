
"""
Window Framework 3.0
"""

__title__ = "window"
__author__ = "fredi_68"
__version__ = "3.0.0"

from .window import Window, ApplicationHandle, EventHandle
from .enums import SDLFlags, SDLDrivers
from .components import Background, Image, Text, HorizontalGradient, VerticalGradient, Surface
from .style import Style, DefaultStyle, StylePackageError, StylePackage
from .errors import WindowError

from . import window, enums, style, ui, components
