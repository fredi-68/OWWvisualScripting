#Window Framework 3.0
"""
Basic components to build complex UI elements from
For more advanced components see UI.py
"""

#FOR FUTURE REFERENCE:
#Don't use subsurfaces as source surfaces in rendering because if screws up our render pipeline if window location and render area don't match up.
#Also it's actually slower. Just don't do it.

import asyncio
import logging

import pygame

from .window import *

class Background(Window):

    """Simple single-color background.
    This class represents a solid colored background that fills the entire window."""

    def __init__(self, pos, width, height, color=[0,0,0]):

        Window.__init__(self, pos, width, height)
        self.color = color
        flags = pygame.SRCALPHA if len(color) > 3 else 0 #set SRCALPHA if an alpha value was specified
        self.surf = pygame.Surface((self.width,self.height), flags)
        self.surf.fill(color)

    async def setColor(self, color):

        """Set the color of the background."""

        self.color = color
        self.surf.fill(color)
        await self.draw()

    async def render(self, area):

        return [[self.surf, [0, 0]]]

class HorizontalGradient(Window):

    """Advanced two-color background.
    This class represents a solid colored background that fills the entire window.
    Its contructor takes two colors which it will fade between to create the gradient.
    The fist color argument specifies the left, the second one the right color."""

    def __init__(self, pos, width, height, colorLeft, colorRight):

        Window.__init__(self, pos, width, height)
        self.colorLeft = colorLeft
        self.colorRight = colorRight
        self.surf = pygame.Surface((self.width,self.height))
        self.slice = pygame.Surface((self.width,1)) #used for gradient calculation
        self._createGradient()

    def _createGradient(self):

        self.surf.fill([0,0,0,0]) #make sure we work with a blank canvas everytime
        self.slice.fill([0,0,0,0])

        #lock surface for pixel access
        self.slice.lock()
        #create gradient by calculating the color steps for each channel for each pixel in a slice
        for i in range(0,self.width):
            self.slice.set_at([i,0],[
                min(max(int(self.colorLeft[0]+(self.colorRight[0]-self.colorLeft[0])*(i/self.width)),0),255),
                min(max(int(self.colorLeft[1]+(self.colorRight[1]-self.colorLeft[1])*(i/self.width)),0),255),
                min(max(int(self.colorLeft[2]+(self.colorRight[2]-self.colorLeft[2])*(i/self.width)),0),255)
                ])
        #unlock surface for blitting
        self.slice.unlock()
        #blit slice onto the surface
        for i in range(0,self.height):
            self.surf.blit(self.slice,[0,i])

    async def changeColorLeft(self, color):

        """Set the left color of the gradient"""

        self.colorLeft = color
        self._createGradient()
        await self.draw()

    async def changeColorRight(self, color):

        """Set the right color of the gradient"""

        self.colorRight = color
        self._createGradient()
        await self.draw()

    async def changeColors(self, colorLeft, colorRight):

        """Set both colors of the gradient"""

        self.colorLeft = colorLeft
        self.colorRight = colorRight
        self._createGradient()
        await self.draw()

    async def swapColors(self):

        """Swap both colors of the gradient"""

        self.colorLeft, self.colorRight = self.colorRight, self.colorLeft
        self._createGradient()
        await self.draw()

    async def render(self, area):

        return [[self.surf, [0, 0]]]

class VerticalGradient(Window):

    """Advanced two-color background.
    This class represents a solid colored background that fills the entire window.
    Its contructor takes two colors which it will fade between to create the gradient.
    The fist color argument specifies the top, the second one the bottom color."""

    def __init__(self, pos, width, height, colorTop, colorBottom):

        Window.__init__(self, pos, width, height)
        self.colorTop = colorTop
        self.colorBottom = colorBottom
        self.surf = pygame.Surface((self.width,self.height))
        self.slice = pygame.Surface((1,self.height)) #used for gradient calculation
        self._createGradient()

    def _createGradient(self):

        self.surf.fill([0,0,0,0]) #make sure we work with a blank canvas everytime
        self.slice.fill([0,0,0,0])

        #lock surface for pixel access
        self.slice.lock()
        #create gradient by calculating the color steps for each channel for each pixel in a slice
        for i in range(0,self.height):
            self.slice.set_at([0,i],[
                min(max(int(self.colorTop[0]+(self.colorBottom[0]-self.colorTop[0])*(i/self.height)),0),255),
                min(max(int(self.colorTop[1]+(self.colorBottom[1]-self.colorTop[1])*(i/self.height)),0),255),
                min(max(int(self.colorTop[2]+(self.colorBottom[2]-self.colorTop[2])*(i/self.height)),0),255)
                ])
        #unlock surface for blitting
        self.slice.unlock()
        #blit slice onto the surface
        for i in range(0,self.width):
            self.surf.blit(self.slice,[i,0])

    async def changeColorTop(self, color):

        """Set the top color of the gradient"""

        self.colorTop = color
        self._createGradient()
        await self.draw()

    async def changeColorBottom(self, color):

        """Set the bottom color of the gradient"""

        self.colorBottom = color
        self._createGradient()
        await self.draw()

    async def changeColors(self, colorTop, colorBottom):

        """Set both colors of the gradient"""

        self.colorTop = colorTop
        self.colorBottom = colorBottom
        self._createGradient()
        await self.draw()

    async def swapColors(self):

        """Swap both colors of the gradient"""

        self.colorTop, self.colorBottom = self.colorBottom, self.colorTop
        self._createGradient()
        await self.draw()

    async def render(self, area):

        return [[self.surf, [0, 0]]]

class Image(Window):

    """Simple image container.
    This class represents an image on the screen. Its source can be any pygame surface, but make sure you call draw() every time its content changes."""

    def __init__(self, pos, image):

        Window.__init__(self, pos, image.get_width(), image.get_height())
        self.surf = image

    async def render(self, area):

        return [[self.surf, [0, 0]]]

    async def setImage(self, image):

        self.surf = image
        await self.draw()

class Surface(Window, pygame.Surface):

    """Advanced image container.
    This class represents a pygame Surface on the screen. It provides all pygame Surface functionality but also exposes the Window Framework API and can be directly
    assigned as a subwindow. Any changes to the Surface will prompt a redraw of the screen."""

    def __init__(self, pos, width, height, flags=0):

        Window.__init__(self, pos, width, height)
        pygame.Surface.__init__((width,height), flags)

    async def render(self, area):

        return [[self, [0, 0]]]

class Text(Window):

    """Simple text display.
    This class represents a text block. Font style, size and color can all be customized."""

    def __init__(self, pos, text="", font=None, size=16, color=[0, 0, 0]):

        self.text = text
        self.font = font
        self.size = size
        self._createFontHandle()
        Window.__init__(self, pos, *self.getTextSize(text)) #dynamically set window size to fit displayed text
        self.color = color
        self.surf = pygame.Surface((self.width,self.height), pygame.SRCALPHA)

        self._createText()

    def _createFontHandle(self):

        self.fontHandle = pygame.font.Font(pygame.font.match_font(self.font) if isinstance(self.font,str) else self.font,self.size) 

    def _createText(self):

        self.surf.fill([0, 0, 0, 0])

        lines = self.text.split("\n")
        for i in range(len(lines)):
            self.surf.blit(self.fontHandle.render(lines[i],True,self.color), [0, self.fontHandle.size(lines[i])[1]*i])

    def getTextSize(self, text):

        """Determine size of text bounding box when drawn to screen.
        Respects newlines."""

        lines = text.split("\n")
        width = 0
        height = 0
        for i in lines:
            linesize = self.fontHandle.size(i)
            if linesize[0] > width:
                width = linesize[0]
            height += linesize[1]

        return (width, height)

    async def setText(self, text):

        """Set the content of the text block."""

        #Here we need to check if the new size or the old size is bigger, then use the
        #larger one to redraw the surface

        area = pygame.Rect((0, 0), self.getTextSize(text))
        area.union_ip(pygame.Rect((0, 0), (self.width, self.height)))

        self.text = text
        self.width, self.height = self.getTextSize(text)
        self.surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._createText()

        #This is a bit of a hack but it works (kind of?) so whatever
        await self._draw(area)
        

    async def setColor(self, color):

        """Set the color of the Text."""

        self.color = color
        self._createText()
        await self.draw()

    async def render(self, area):

        return [[self.surf, [0, 0]]]
