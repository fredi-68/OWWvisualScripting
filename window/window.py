#Window Framework 3.0
#Now with asyncio support!

"""This file contains the Window framework and everything necessary to build asyncroneous rendering engines using pygame that offer a lot of freedom.
For a more easy to use approach see components.py and UI.py"""

import asyncio
import logging
import os

import pygame

from .enums import SDLFlags, SDLDrivers
from .style import DefaultStyle

logger = logging.getLogger("window framework")

#CUSTOM PYGAME EVENTS

EVENT_APP_STARTED = pygame.USEREVENT+1
EVENT_APP_STOPPED = pygame.USEREVENT+2
EVENT_MOUSE_ENTERED = pygame.USEREVENT+3
EVENT_MOUSE_LEFT = pygame.USEREVENT+4

if not pygame.display.get_init():
    pygame.display.init() #initialize display, otherwise creating the default style will raise an exception
    pygame.font.init()
DEFAULT_STYLE = DefaultStyle()

def setDefaultStyle(defaultStyle):
    global DEFAULT_STYLE
    DEFAULT_STYLE = defaultStyle

def makeEvent(type, attr={}):

    """Shorthand for pygame.event.Event(type,attr)"""

    return pygame.event.Event(type,attr)

def postEvent(type, attr={}):

    """Shorthand for pygame.event.post(pygame.event.Event(type, attr))"""

    pygame.event.post(makeEvent(type, attr))

def _setWinDPIAware():

    import ctypes

    ctypes.windll.user32.SetProcessDPIAware() #turn off windows DPI auto scaling

    #cleanup
    del ctypes

DEBUG_LAYOUT = False

def setLayoutDebugMode(active):

    global DEBUG_LAYOUT
    DEBUG_LAYOUT = active
    logger.info("Set Window Framework layout boundary debug display to "+str(active))

class Window():

    """
    Represents a Window on screen.
    This class manages a rectangular window. It can be anywhere on or off screen. It takes care of drawing and handling events.
    """

    logger = logging.getLogger("WINDOW")

    def __init__(self, pos, width, height):

        self.pos = pos
        self.subwindows = []
        self.width = width
        self.height = height
        self.parent = None
        self.mouse_in_frame = False
        self.visible = True
        self.connectedSurface = None

        self.style = DEFAULT_STYLE

    def addObject(self, obj):

        """
        Add an object to the internal subwindow list.
        obj should be an instance of window or a
        derived class of it
        """

        if isinstance(obj,Window):
            self.subwindows.append(obj)
            obj.setParent(self) #add parent reference (this will be important for drawing later)

    def removeObject(self, obj):

        """
        Remove a subwindow from this window.
        obj must be of type window or a subclass of it and
        be a subwindow of this window
        """

        if obj in self.subwindows:
            self.subwindows.remove(obj)
            obj.setParent(None)
            return True
        return False

    def setParent(self, parent):

        """
        Set the parent window of this window.
        The user should not usually interface with this method directly, instead it is handled by the addObject and removeObject methods.
        """

        self.parent = parent
        
    def _getRoot(self):

        """
        Get the root Window (top of the list, usually connected to a surface)
        """

        return self.parent._getRoot() if self.parent else self

    def isRoot(self):

        """
        Determine if this window is a root window.
        """

        return True if self.parent else False

    def connectSurface(self, surf):

        """
        Register a surface to be rendered into when the draw() method is called.
        This will dump every drawing action performed on this window and all subwindows to the surface specified.
        While this can be used to extract window content from anywhere in the window stack, this would be very resource intensive to do, thus it is highly discouraged.
        """

        if isinstance(surf, pygame.Surface):
            self.connectedSurface = surf
            if self.parent:
                self.logger.warn(repr(surf)+" was connected to "+repr(self)+" even though it isn't the root Window!")
        else:
            raise ValueError("surf must be of type "+str(type(pygame.Surface))+"!")

    async def render(self, area):

        """
        Called by the root window if something needs to be rendered to screen.
        area specifies the position as well as width and height of the rendered area.
        This method should return a list of surfaces to be rendered FIFO. Surfaces will be truncated if they exceed area limits.
        """

        return []

    async def _render(self, area):

        """
        Internal method.
        """

        #This is where things get difficult.
        #It's not enough to check if the area lies WITHIN the window boundaries, this condition has to be True whenever the area and the window share ANY content.
        #This means the area could also be bigger than this window or only a part of both could match.
        newarea = area.clip(pygame.Rect(self.pos,[self.width,self.height]))
        if newarea and self.visible:
            #If the area is within window boundaries, query all subwindows to render.
            #also call our own render method

            newarea.move_ip([-self.pos[0],-self.pos[1]])

            try:
                comp = await self.render(newarea)
            except pygame.error as e: #This is most likely to happen during shutdown when coroutines try to access the screen
                self.logger.error("An error occured in the graphics pipeline: "+str(e))
            
            for win in self.subwindows:
                comp.extend(await win._render(newarea))

            for c in comp:
                c[1][0] += self.pos[0]
                c[1][1] += self.pos[1]

            return comp
        #Area is outside of window boundaries, return an empty list
        return []

    async def draw(self):

        """
        Redraws the part of the screen that is occupied (or partially occupied) by this Window.
        This will also do the right thing if the background is updated.
        Call this every time the content of this window changes.
        The smaller the size of the window, the smaller the performance impact will be.
        """

        await self._draw(pygame.Rect(0,0,self.width,self.height)) #initialize redraw

    async def _draw(self, area):

        """
        Internal method.
        area should be an area of this window that needs to be updated.
        """

        if self.parent:
            area.move_ip(self.pos[0], self.pos[1])
            await self.parent._draw(area)

        if self.connectedSurface:
            #render windows to surface

            for i in await self._render(area):

                #So, I finally figured out how clipping rectangles work in pygame...
                #The clipping area is relative to the SOURCE surface, NOT the destination.
                #So, to do efficient rendering we need to move the clipping area in local space of the source,
                #then move the resulting clipped image back to global space. We do this by moving the area using the
                #coordinates of the source, then add the location of the source to the location of the clipping rect
                #(since we subtracted it before). To make things a bit easier on the eyes I put the respective
                #calculations on separate lines.

                clippingArea = area.move(-i[1][0], -i[1][1])
                renderpos = [i[1][0]+clippingArea.left, i[1][1]+clippingArea.top]

                try:
                    self.connectedSurface.blit(i[0], renderpos, clippingArea) #blit surfaces to the connected Surface
                except pygame.error as e: #This is most likely to happen during shutdown when coroutines try to access the screen
                    self.logger.error("An error occured in the graphics pipeline: "+str(e))
                    return #cancel operation

            if DEBUG_LAYOUT:
                #Shows the drawing boundaries of window updates
                pygame.draw.rect(self.connectedSurface, (255, 0, 0), area, 1)

            if self.connectedSurface == pygame.display.get_surface():
                #Update screen
                try:
                    pygame.display.update(area)
                except: #This can happen if we are using hardware surfaces, for example with OpenGL
                    pass #We can't do pygame.display.flip() here because that may cause it to be called multiple times per frame and I am PRETTY SURE that won't do what it should.

    async def toggleVisibility(self):

        """
        Toggle the visibility of the window.
        An invisible window will not be drawn to the screen.
        This method will automatically redraw the screen.
        """

        self.visible = not self.visible
        await self.draw()

    #EVENT HANDLING

    async def handleEvent(self,event):

        """
        Event handler method. This is called every time an unhandled event is triggered.
        Users should override this if they want more precise control over events than the event listener system allows them to have.
        If this method returns False, the internal event handler will take care of properly handling the event, if it returns True this behaviour will be skipped.
        This is true for all other event handler methods as well.
        """

        return await self._handleEvent(event)

    def pointInWindow(self, pos):

        """
        Return True if the specified point lies within this window, False otherwise.
        """

        return self.pos[0] <= pos[0] <= self.pos[0] + self.width and self.pos[1] <= pos[1] <= self.pos[1] + self.height

    def posLocalToGlobal(self, pos):

        """
        Translate a local position into global screen space.
        """

        if not self.parent:
            #is root
            return pos
        return self.parent.posLocalToGlobal([pos[0]+self.pos[0], pos[1]+self.pos[1]])

    def posGlobalToLocal(self, pos):

        """
        Translate a global position into local space.
        """

        if not self.parent:
            #is root
            return pos
        return self.parent.posLocalToGlobal([pos[0]-self.pos[0], pos[1]-self.pos[1]])

    @property
    def center(self):

        """
        Return the center position of this window.
        """

        return [self.pos[0]+self.width/2, self.pos[1]+self.height/2]

    async def setPos(self, pos):

        if len(pos) != 2:
            raise ValueError("position must be a sequence of two numbers")

        pos = list(map(int, pos))

        oldpos = [self.pos[0] - pos[0], self.pos[1] - pos[1]]
        print(oldpos)
        self.pos = pos

        await self.draw()
        await self._draw(pygame.Rect(oldpos, (self.width, self.height))) #make sure the old position is updated as well

    async def setCenter(self, pos):

        """
        Set the center position of this window.
        """

        await self.setPos([pos[0]-self.width/2, pos[1]-self.height/2])

    async def _handleEvent(self,event):

        """
        Internal event handler. Users should not have to interface with this directly. Instead, use the event listener system or handleEvent() for more control.
        """

        reverse_subwindows = self.subwindows.copy()
        reverse_subwindows.reverse()

        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):

            #For mouse events we want the user to interface with the provided convenience methods instead of manually checking positioning and events.
            #This means that the event handler has to check if the mouse event occured within this window. If it did, we should call the respective
            #event handler method for that event. If it returns True, nothing else has to be done (although we will return True as well to signal the other
            #windows that this even has already been handled). If it returns False, we propagate the event to our subwindows with realigned position values
            #to match their position relative to this window. If any of the subwindows event handlers return True for this event we skip the others and return
            #True as well, otherwise we return False.
            #If the event occured outside of this windows boundaries, we call the onMouseLeave method and send a EVENT_MOUSE_LEFT to all subwindows to signal
            #them that the mouse has left this area of the screen.
            #NOTE: onMouseEnter and onMouseLeave should only be called once the mouse_in_frame state changes to prevent code from being executed to often. This
            #means that if our mouse_in_frame state is False and we receive a mouse event that is outside of window boundaries we don't have to dispatch a 
            #EVENT_MOUSE_LEFT event since all subwindows should know about it already. Same for if we receive such an event ourselves.)


            orgpos = event.pos
            relpos = [orgpos[0]-self.pos[0],orgpos[1]-self.pos[1]] #calculate relative event position
            if self.pointInWindow(orgpos):
                #Event occured within window boundaries

                if not self.mouse_in_frame:

                    #call mouse enter event first in case it needs to set something up
                    await self.onMouseEnter(event)
                    self.mouse_in_frame = True #set new state

                #Generate new event
                attr = event.dict.copy()
                attr["pos"] = relpos
                newevent = makeEvent(event.type, attr)

                #call convenience methods
                returned = False

                if event.type == pygame.MOUSEBUTTONDOWN:

                    returned = await self.onMouseButtonDown(newevent)

                elif event.type == pygame.MOUSEBUTTONUP:

                    returned = await self.onMouseButtonUp(newevent)

                elif event.type == pygame.MOUSEMOTION:

                    returned = await self.onMouseMotion(newevent)

                if returned:

                    #Event handler consumed event, return
                    return True
                
                #propagate event
                for i in reverse_subwindows:
                    if await i.handleEvent(newevent):
                        return True
                return False #Subwindows did not consume the event, return False

            #Event occured outside of window boundaries

            await self._handleMouseLeave()

        elif event.type == EVENT_MOUSE_LEFT:

            await self._handleMouseLeave() #make sure we (and all other subwindows) are aware of the mouse leaving the window

        elif event.type == pygame.KEYDOWN:

            #Handle keystroke and propagate event

            if await self.onKeystroke(event):
                return True
            for i in reverse_subwindows:
                if await i.handleEvent(event):
                    return True
            return False

        else:

            #Propagate event

            for i in reverse_subwindows:
                if await i.handleEvent(event):
                    return True
            return False

    async def _handleMouseLeave(self):

        if self.mouse_in_frame:
            #Mouse just left window

            await self.onMouseLeave(None) #call mouse event method
            self.mouse_in_frame = False #set new state

            for i in self.subwindows:
                await i.handleEvent(makeEvent(EVENT_MOUSE_LEFT,{}))

    async def onMouseButtonDown(self, event):

        """Convenience method.
        This method is called every time a mouse button is clicked in this window or a subwindow."""

        return False

    async def onMouseButtonUp(self, event):

        """Convenience method.
        This method is called every time a mouse button is let up on in this window or a subwindow."""

        return False

    async def onMouseMotion(self, event):

        """Convenience method.
        This method is called every time the mouse is moved in this window or a subwindow."""

        return False

    async def onMouseEnter(self, event):

        """Convenience method.
        This method is called every time the mouse cursor enters this window."""

        return False

    async def onMouseLeave(self, event):

        """Convenience method.
        This method is called every time the mouse cursor leaves this window.
        Since this event occurs outside of the window, event will always be None but it is kept in for method signature consistency."""

        return False

    async def onKeystroke(self, event):

        """Convenience method.
        This method is called every time the user presses a key and the window has input focus."""

        pass

    #SPECIAL METHODS

    def __repr__(self, *args, **kwargs):

        #We interpret a window as root window if it doesn't have any parent window.
        #There can be multiple root windows in one application.
        #NOTE: root window in this context does not equal ApplicationHandle root window.
        return "<"+("" if self.parent else "Root")+"Window object "+str(id(self))+" ("+str(self.width)+"x"+str(self.height)+"@"+str(self.pos)+")>"

    def __str__(self, *args, **kwargs):

        return self.__repr__()

    def __eq__(self, obj):

        if isinstance(obj, Window):
            return self.width == obj.width and self.height == obj.height and self.pos == obj.pos and self.visible == obj.visible and self.parent == obj.parent
        else:
            return False

    def __ne__(self, obj):

        return not self.__eq__(obj)

    def __bool__(self):

        return self.visible

    def __lt__(self, obj):

        if not isinstance(obj, Window):
            raise ValueError("types "+str(type(obj))+" and "+str(type(self))+" are not comparable!")
        return self.width*self.height < obj.width*obj.height

    def __le__(self, obj):

        if not isinstance(obj, Window):
            raise ValueError("types "+str(type(obj))+" and "+str(type(self))+" are not comparable!")
        return self.width*self.height <= obj.width*obj.height

    def __gt__(self, obj):

        if not isinstance(obj, Window):
            raise ValueError("types "+str(type(obj))+" and "+str(type(self))+" are not comparable!")
        return self.width*self.height > obj.width*obj.height

    def __ge__(self, obj):

        if not isinstance(obj, Window):
            raise ValueError("types "+str(type(obj))+" and "+str(type(self))+" are not comparable!")
        return self.width*self.height >= obj.width*obj.height

class EventHandle():

    """Event handle.
    Looks for an event of type <type> and a list of attributes matching the <attr> dictionary and calls <callback> everytime this event is triggered.
    <callback> must be a coroutine. It will be called with the event as a single argument. If the callback returns True, event handling will be terminated
    for the current event. Use this to signal the event system to stop propagating an event that has already been fully handled, this can cut down on
    per frame computation time."""

    logger = logging.getLogger("EVENT")

    def __init__(self, type, attr, callback):

        self.type = type
        self.attr = attr
        self.callback = callback

    async def _handleEvent(self, event):

        if event.type == self.type:
            for item in self.attr.items():
                if (not item[0] in event.__dict__) or (not item[1] == event.__dict__[item[0]]):
                    return False
            self.logger.debug("Conditions triggered for "+str(self))
            try:
                return await self.callback(event) #wait for the callback to exit
            except:
                self.logger.exception("An unhandled exception occured in EventHandle callback")
            return False #This should only trigger if the callback failed so we tell the event handler to propagate the event

    def __repr__(self):

        return "<EventHandle (type "+str(self.type)+", attributes: "+repr(self.attr)+")>"

class ApplicationHandle():

    """Application Handle
    This class represents the entire application and provides access to the event handlers, displays and the event loop.
    It also manages the connections between asyncio, Pygame and other libraries.
    Setting up a Window Framework 3.0 Application can be as easy as just making an instance of the ApplicationHandle and calling its start() method.
    This will prompt the application to enter the event loop, blocking excecution of further instructions until application termination.
    All user interaction is either done by the windows contained in the application or registered event handlers.
    For more control, the user may also specify custom coroutines that can be excecuted in the event loop. The event loop can be customized as well."""

    def __init__(self, size=None, loop=None):

        pygame.init()

        self.screen = None
        self.size = size if size else pygame.display.list_modes()[0] #make sure we have a size
        self.displayFlags = 0
        self.SDLFLags = {}
        self.displayCaption = None
        self.loop = loop

        #We need to set a maximum tickrate so the asyncio loop knows when to schedule the renderer and event collection calls.
        #There is no way to deactivate it, but setting it to a ridiculously high count will most likely get the job done
        #This is frames per second so a value of ~10000 should be enough to guarantee smoothness I recon :P
        #NOTE: This is the MAXIMUM frame rate and the guaranteed tickrate of the event processor, the actual framerate of the application may be significantly lower
        #due to nothing happening to the window (or higher due to parallel window redraws, cause I still haven't fixed that yet).
        self.tickrate = 200

        self.root = None

        self.eventHandles = []
        self.cleanUpHandles = []

        self.logger = logging.getLogger(str(self))

    def registerEventHandle(self, handle):

        """Add an EventHandle to the event processor.
        If the handle is already registered this call will fail silently."""

        if not isinstance(handle, EventHandle):
            raise ValueError("handle must be an EventHandle instance!")

        if not handle in self.eventHandles:
            self.eventHandles.append(handle)

    def unregisterEventHandle(self, handle):

        """Remove the EventHandle from the event processor.
        handle must be a registered EventHandle object."""

        if not handle in self.eventHandles:
            raise ValueError("EventHandle is not registered to this ApplicationHandle!")
        self.eventHandles.remove(handle)

    def setDisplayCaption(self, caption):

        """Set the title of the pygame window"""
        if not isinstance(caption, str):
            raise ValueError("caption must be a string!")
        
        self.displayCaption = caption

        if self.isRunning():
            pygame.display.set_caption(self.displayCaption)

        self.logger = logging.getLogger(str(self)) #refresh logger name

    def setDisplayFlags(self, flag, value=""):

        """Set the display flags to use when initializing the display mode.
        This method can also be used to set environmental attributes for the SDL backend.
        For this, one should use the provided SDLFlags enum. In this case, the value of the flag should be
        specified as the value argument"""

        if isinstance(flag, int):
            self.displayFlags = flag

        elif isinstance(flag, SDLFlags):
            self.SDLFLags[flag.value] = value

        else:
            raise ValueError("flags must be either of type int or SDLFlags!")

    async def _processEvents(self):

        while self.loop.is_running():
            await asyncio.sleep(1/self.tickrate)
            for event in pygame.event.get():

                handled = False
                for handle in self.eventHandles:
                    if await handle._handleEvent(event):
                        handled = True
                        break
                if not handled: #Send event to the windows
                    await self.root.handleEvent(event)

    async def postEvent(self, event):

        """Send an event to the handlers."""

        for handle in self.eventHandles:
            await handle._handleEvent(event)

    async def _resizeWindow(self, newsize):

        pass

    def setRoot(self, root):

        """Set the root window of this application.
        This method should ONLY be called if a customized root window is ABSOLUTELY necessary,
        since the root window set up by the ApplicationHandle is already configured to work with the current display configuration."""

        if not isinstance(root, Window):
            raise ValueError("root must be of type Window!")
        self.root = root

    def _createRootWindow(self):

        self.root = Window([0, 0], self.size[0], self.size[1])
        if self.screen:
            self.root.connectSurface(self.screen)
        return self.root

    def getRoot(self, forcenew=False):

        """Get the root window of this ApplicationHandle. If already configured, this will return the existing window unless forcenew is True.
        Otherwise it will return a new root window configured to be used for display rendering."""

        if not self.root == None:
            if forcenew:
                return self._createRootWindow()
            return self.root
        return self._createRootWindow()

    def start(self):

        """
        Start the application. If no event loop was specified, this call will block.
        WARNING: If you are using a custom event loop, you are responsible for starting
        it as soon as possible. If you don't do this, pygames event queue will fill up
        quickly and the window will become unresponsive.
        """

        self.logger.info("Starting up...")

        #Question: Do we need to reinit pygame to commit SDL environment variables?
        #Answer: Nope.
        if len(self.SDLFLags) > 0:
            self.logger.info("Setting SDL display flags...")
            for i in self.SDLFLags.items():
                os.environ[i[0]] = i[1] #set SDL environment variables

        self.logger.debug("Setting display mode...")
        self.screen = pygame.display.set_mode(self.size, self.displayFlags)

        pygame.scrap.init() #eurgh...

        if self.root == None:
            self.logger.debug("No root window set, creating a new one...")
            self._createRootWindow() #Now is the best time to initialize our root window if we haven't already done this.
        else:
            self.root.connectSurface(self.screen)

        if self.displayCaption:
            pygame.display.set_caption(self.displayCaption)

        if self.loop:
            #we already have an event loop, it is up to the user to start it (or pehaps it already has)
            self.loop.create_task(self._processEvents())
            self.loop.create_task(self.postEvent(makeEvent(EVENT_APP_STARTED))) #Notify startup handles
            self.loop.create_task(self.root.draw()) #Initial draw
            self.logger.info("Ready")
        else:
            self.loop = asyncio.get_event_loop() #create new event loop
            self.loop.create_task(self._processEvents())
            self.loop.create_task(self.postEvent(makeEvent(EVENT_APP_STARTED))) #Notify startup handles
            self.loop.create_task(self.root.draw()) #Initial draw
            self.logger.info("Running")
            self.loop.run_forever()#run until program is complete

    def stop(self):

        """Shut down application and free all resources. This will also stop the event loop."""

        self.logger.info("Stopping...")
        self.logger.debug("Running clean up functions...")
        for i in self.cleanUpHandles:
            try:
                i()
            except:
                self.logger.exception("An unhandled exception occured in clean up handler")
        if self.loop.is_running():
            self.loop.stop()
        self.logger.debug("Deinitializing Pygame...")
        pygame.quit() #make sure we stop all coroutines possibly making calls to pygame before we shut it down
        self.logger.info("Stopped")

    def isRunning(self):

        """Determine if the application is currently running.
        NOTE: This method returns True as long as the pygame display is active."""

        return pygame.display.get_init() and (pygame.display.get_surface() != None)

    #SPECIAL METHODS

    def __str__(self, **kwargs):
        
        return "<ApplicationHandle "+(pygame.display.get_caption()[0] if pygame.display.get_caption() else "untitled")+"@"+str(self.size[0])+"x"+str(self.size[1])+">"

if os.name == "nt":
    import sys

    if sys.getwindowsversion()[0] >= 6:
        logger.debug("Detected Windows operating system Vista or greater. Attempting to deactivate DPI autoscaling...")

        try:
            _setWinDPIAware()
            logger.debug("Success!")
        except Exception as e:
            logger.debug("Failed to deactivate DPI autoscaling: "+str(e))

    #clean up
    del sys
