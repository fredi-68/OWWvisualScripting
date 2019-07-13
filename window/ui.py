#Window Framework 3.0

"""More complex UI components to quickly build applications from scratch that provide advanced funtionality"""

import asyncio
import logging

import pygame
import numpy

from .window import Window
from .components import Background, HorizontalGradient, Image, Surface, Text, VerticalGradient

#MIXINS

class _Menu(Window):

    def __init__(self, pos, master, entries, font, fontSize):

        self.entries = entries
        self.fontSize = fontSize
        _entries = []
        y = 0
        for i in entries:
            if isinstance(i, str):
                text = Text([0, y*fontSize], i, color=(200, 200, 200), size=fontSize)
            else:
                text = Text([0, y*fontSize], i[0], color=(200, 200, 200), size=fontSize)
            _entries.append(text)
            y += 1
        width = max(map(lambda x: x.width, _entries))
        height = len(_entries) * fontSize
        super().__init__(pos, width, height)
        self.master = master

        self.bg = Background([0, 0], self.width, self.height, (100, 100, 100))
        self.addObject(self.bg)

        for i in _entries:
            self.addObject(i)

    async def handleEvent(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not self.pointInWindow(event.pos):
                    await self.close() #Close the window whenever a mouseclick happens outside of this window
                    return False

        return await self._handleEvent(event)

    async def onMouseButtonDown(self, event):

        if event.button == 1:
            i = event.pos[1] // self.fontSize
            entry = self.entries[i]
            #TODO: Add handling of submenus
            await self.master.onMenuSelect(entry)
            await self.close()

    async def close(self):

        parent = self.parent
        self.parent.removeObject(self)
        await parent.draw()

class Menu(Window):

    """
    Window mixin class.
    This is meant to be subclassed. Use this class instead of window.Window wherever you
    want the option of opening a menu (be it in a menu bar or using a righclick context menu style).
    This class manages all the complicated matters of positioning the menu above other windows and making
    sure it draws at the right place.

    Two methods are available to create and interact with menus:
    showMenu() creates a new menu
    handleMenuSelect() implements handling for user selection

    Don't worry about how it works.
    """

    async def showMenu(self, entries, fontSize=20):

        """
        Open a menu at the location of this window.
        A menu will be created automatically and shown to the user.
        Once an item has been selected, the menu will close and self.handleMenuSelect() will be called with the selected
        entry/submenu items passed as a list.

        entries should be a list of strings and/or lists.
        each string represents a clickable entry, each list represents a submenu that itself is another menu.
        Each lists first element must be a string, this will be used as the name of the menu (in submenus, this will be
        the name of the element in the parent menu that opens this menu).
        Each list will be passed to a new menu instance recursively. Example:

        [
            "A menu",
            "A value",
            [
                "A submenu",
                "A value in a submenu",
                [
                    "A submenu in a submenu",
                    "A value in a submenu in a submenu",
                    "Another value"
                ]
            ]
        ]

        Entries will appear in the order they were entered into the list.
        """

        menu = _Menu(self.posLocalToGlobal([0, self.height]), self, entries, None, fontSize)
        self._menu = menu
        self._getRoot().addObject(menu)
        await menu.draw()

    async def onMenuSelect(self, entry):

        """
        Override this to handle menu selections.
        entry is a list of strings, each string representing the menu that the user selected.
        The last entry is always the menu item the user clicked on.
        If entry only has one element, no submenus were used.
        """

        pass

#BUTTONS

class Button(Window):

    """A simple button.
    This class draws a button and takes care of all necessary event handling.
    To ensure that overriding onMouseButtonDown() doesn't mess up this classes internal event handling, you can override onButtonHit() instead."""

    def __init__(self, pos, width, height, label="", font=None, fontColor=[255,255,255], fontSize=12, bgColor=[100,100,100], bgHoverColor=[200,200,200], bgClickColor=[80,80,80], image=None, hoverImage=None, clickImage=None, centerLabel=True):

        Window.__init__(self, pos, width, height)

        self.bgColor = bgColor
        self.bgHoverColor = bgHoverColor
        self.bgClickColor = bgClickColor

        self.image = image
        self.imageHover = hoverImage
        self.imageClick = clickImage

        self.bg = Background([0, 0], self.width, self.height, self.bgColor)
        self.addObject(self.bg)

        self.bgImage = Image([0, 0], self.image) if self.image else None
        if self.bgImage:
            self.addObject(self.bgImage)

        self.label = Text([0,0], label, font, fontSize, fontColor)
        if centerLabel:
            textpos = [int(width/2-self.label.width/2), int(height/2-self.label.height/2)]
            self.label.pos = textpos
        self.addObject(self.label)

    async def onMouseEnter(self, event):
        
        await self.bg.setColor(self.bgHoverColor)
        if self.bgImage and self.imageHover:
            await self.bgImage.setImage(self.imageHover)
        return False

    async def onMouseLeave(self, event):

        await self.bg.setColor(self.bgColor)
        if self.bgImage and self.image:
            await self.bgImage.setImage(self.image)
        return False

    async def onMouseButtonDown(self, event):

        await self.bg.setColor(self.bgClickColor)
        if self.bgImage and self.imageClick:
            await self.bgImage.setImage(self.imageClick)
        return await self.onButtonHit(event)

    async def onMouseButtonUp(self, event):

        await self.bg.setColor(self.bgColor)
        if self.bgImage and self.image:
            await self.bgImage.setImage(self.image)

    async def onButtonHit(self, event):

        return False

class ToggleButton(Button):

    """A button that can be toggled between two states (on/off button or switch).
    This class draws a toggle button and takes care of all necessary event handling"""

    def __init__(self, pos, width, height, bgActiveColor=[150,150,150], activeImage=None, activeHoverImage=None, **kwargs):

        Button.__init__(self, pos, width, height, **kwargs)
        self.bgActiveColor = bgActiveColor
        self.activeImage = activeImage
        self.activeHoverImage = activeHoverImage
        self.active = False

    async def onMouseEnter(self, event):
        
        await self.bg.setColor(self.bgHoverColor)
        if self.bgImage and self.imageHover and self.activeHoverImage:
            await self.bgImage.setImage(self.activeHoverImage if self.active else self.imageHover)
        return False

    async def onMouseLeave(self, event):

        await self.bg.setColor(self.bgActiveColor if self.active else self.bgColor)
        if self.bgImage and self.activeImage and self.image:
            await self.bgImage.setImage(self.activeImage if self.active else self.image)
        return False

    async def onMouseButtonDown(self, event):

        await self.setState(not self.active)
        return await self.onButtonHit(event)

    async def onMouseButtonUp(self, event):

        pass

    async def setState(self, state):

        self.active = state
        await self.bg.setColor(self.bgActiveColor if self.active else self.bgColor)
        if self.bgImage and self.activeImage and self.image:
            await self.bgImage.setImage(self.activeImage if self.active else self.image)

class _CheckboxButton(ToggleButton):

    def __init__(self, pos, width, height, image, activeImage, hoverImage, activeHoverImage, default):

        ToggleButton.__init__(self, pos, width, height, image=image, activeImage=activeImage, hoverImage=hoverImage, activeHoverImage=activeHoverImage)
        if default:
            self.active = True
            self.bgImage.surf = activeImage

class CheckboxArray(Window):

    """A set of checkboxes (Multiple choice).
    This class automatically creates and arranges the necessary buttons and provides a simple interface for retrieving the results.
    size specifies the size of the checkboxes, not the size of the resulting array bounding box."""

    def __init__(self, pos, size=30, options = [], defaults=[], bgColor=[50,50,50], bgHoverColor=[100,100,100], checkmarkColor=[255,255,255], labelColor = [200,200,200]):

        if len(options) < 1:
            raise ValueError("options must have at least one element")
        if len(defaults) < len(options):
            for i in range(len(options) - len(defaults)):
                defaults.append(False)

        fieldPadding = size//5

        fieldBg = pygame.Surface((size, size))
        fieldBg.fill(bgColor)

        fieldHoverBg = pygame.Surface((size, size))
        fieldHoverBg.fill(bgHoverColor)

        fieldActiveBg = pygame.Surface((size, size))
        fieldActiveBg.fill(bgColor)
        pygame.draw.line(fieldActiveBg, checkmarkColor, [fieldPadding, fieldPadding], [size-fieldPadding, size-fieldPadding], size//10)
        pygame.draw.line(fieldActiveBg, checkmarkColor, [fieldPadding, size-fieldPadding], [size-fieldPadding, fieldPadding], size//10)

        fieldActiveHoverBg = pygame.Surface((size, size))
        fieldActiveHoverBg.fill(bgHoverColor)
        pygame.draw.line(fieldActiveHoverBg, checkmarkColor, [fieldPadding, fieldPadding], [size-fieldPadding, size-fieldPadding], size//10)
        pygame.draw.line(fieldActiveHoverBg, checkmarkColor, [fieldPadding, size-fieldPadding], [size-fieldPadding, fieldPadding], size//10)

        maxwidth = 0

        self.options = {}
        self.labels = []
        for i in range(len(options)):
            cb = _CheckboxButton([0, i*(size+5)], size, size, fieldBg, fieldActiveBg, fieldHoverBg, fieldActiveHoverBg, defaults[i])
            self.options[options[i]] = cb
            label = Text([size+5, i*(size+5)], options[i], size=size, color=labelColor)
            self.labels.append(label)
            if label.width > maxwidth:
                maxwidth = label.width

        Window.__init__(self, pos, maxwidth+size+5, len(options) * (size+5))
        for i in self.options.values():
            self.addObject(i)

        for i in self.labels:
            self.addObject(i)

    def getState(self, option):

        if not option in self.options:
            raise KeyError("This option doesn't exist in this CheckboxArray")
        return self.options[option].active

    async def setState(self, option, state):

        if not option in self.options:
            raise KeyError("This option doesn't exist in this CheckboxArray")
        return await self.options[option].setState(state)

class RadioboxArray(Window):

    """A set of radioboxes (Single choice)
    This class automatically creates and arranges the necessary buttons and provides a simple interface for retrieving the results."""

    pass

#INPUT FIELDS

class DropDownField(Menu):

    """
    A dropdown field that allows a user to select one of multiple supported values.
    """

    def __init__(self, pos, width, height, values=[], default="", textColor=[200, 200, 200], bgColor=[0, 0, 0], bgHoverColor=[100, 100, 100]):

        super().__init__(pos, width, height)
        self.bgColor = bgColor
        self.hoverColor = bgHoverColor
        self.bg = Background([0, 0], width, height, bgColor)
        self.addObject(self.bg)
        self.values = values

        self.text = Text([0, 0], default, color=textColor, size=height)
        self.addObject(self.text)

    async def onMouseButtonDown(self, event):

        if event.button == 1:
            await self.showMenu(self.values, self.height)

    async def onMouseMotion(self, event):

        await self.bg.setColor(self.hoverColor)

    async def onMouseLeave(self, event):

        await self.bg.setColor(self.bgColor)

    async def onMenuSelect(self, entry):

        await self.text.setText(entry)
        await self.onValueChange(entry)

    async def onValueChange(self, value):

        pass

class TextField(Window):

    """A writeable textfield for basic user input.
    This class draws a textfield and will take care of the common even handling users would expect from a textfield."""

    def __init__(self, pos, width, height, defaultText="", textColor=[200,200,200], bgColor=[0,0,0], bgHoverColor=[100,100,100], bgClickColor=[50,50,50]):

        Window.__init__(self, pos, width, height)

        self.bg = Background([0, 0], width, height, color=bgColor)
        self.addObject(self.bg)

        self.bgColor = bgColor
        self.bgHoverColor = bgHoverColor
        self.bgClickColor = bgClickColor

        self.text = Text([0,0], defaultText, color=textColor, size=height)
        self.addObject(self.text)

    def getText(self):

        """
        Return the text stored in the internal buffer.
        """

        return self.text.text

    async def _addCharacter(self, character):

        await self.text.setText(self.text.text+character)

    async def _removeCharacter(self):

        if len(self.text.text) > 0:
            await self.text.setText(self.text.text[:-1])

    async def filterInput(self, character):

        """Override this method to implement character filtering.
        Returns True if the entered character is valid."""

        return character.isprintable()

    async def onKeystroke(self, event):

        if not self.mouse_in_frame:
            return False

        if event.key == pygame.K_BACKSPACE:
            await self._removeCharacter()
            return True

        #pasting things
        if (pygame.key.get_mods() & pygame.KMOD_CTRL) and event.key == pygame.K_v:
            #if not pygame.scrap.contains(pygame.SCRAP_TEXT):
            #    return True

            data_in = ""
            for i in pygame.scrap.get(pygame.SCRAP_TEXT).decode():
                if await self.filterInput(i):
                    data_in += i

            await self.text.setText(self.text.text + data_in)
        
        else:
            if await self.filterInput(event.unicode):
                await self._addCharacter(event.unicode)
                return True

    async def onMouseEnter(self, event):
        
        await self.bg.setColor(self.bgHoverColor)
        return False

    async def onMouseLeave(self, event):

        await self.bg.setColor(self.bgColor)
        return False

    async def onMouseButtonDown(self, event):

        await self.bg.setColor(self.bgClickColor)

class NumberField(TextField):

    """A writeable textfield for basic user input.
    Like TextField but will ensure that only numbers are allowed in the input."""

    async def filterInput(self, character):

        """Override this method to implement character filtering.
        Returns True if the entered character is valid."""

        return character in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ".")

class PasswordField(TextField):

    """A writeable textfield for basic user input.
    Like TextField but will replace any character with an asterisk ("*") in the UI element."""

    def __init__(self, pos, width, height, **kwargs):

        TextField.__init__(self, pos, width, height, **kwargs)
        self.internalText = self.text.text

    def getText(self):

        """
        Return the text stored in the internal buffer.
        """

        return self.internalText

    async def _addCharacter(self, character):

        if character:
            await self.text.setText(self.text.text+"*")
        self.internalText += character

    async def _removeCharacter(self):

        if len(self.text.text) > 0:
            await self.text.setText(self.text.text[:-1])
            self.internalText = self.internalText[:-1]

    async def onKeystroke(self, event):

        if not self.mouse_in_frame:
            return False

        #pasting things
        if (pygame.key.get_mods() & pygame.KMOD_CTRL) and event.key == pygame.K_v:
            #if not pygame.scrap.contains(pygame.SCRAP_TEXT):
            #    return True

            data_in = ""
            for i in pygame.scrap.get(pygame.SCRAP_TEXT).decode():
                if await self.filterInput(i):
                    data_in += i

            self.internalText += data_in
            await self.text.setText(self.text.text + "*"*len(data_in))
        
        else:
            return await TextField.onKeystroke(self, event)

class _EntryContainer(Window):

    def __init__(self, pos, width, height, entry):

        Window.__init__(self, pos, width, height)

        self.entry = entry
        self.bg = Background([0, 0], width, height, self.style.getColor("bg2", self))
        self.addObject(self.bg)

        self.text = Text([0, 0], entry, size=height, color=self.style.getColor("text", self))
        self.addObject(self.text)

        self.active = False

    async def setState(self, active):

        if self.active == active: #Save performance if we don't actually have to change anything
            return
        self.active = active
        await self.bg.setColor(self.style.getColor(("select" if self.active else "bg2"), self.bg))

    async def onMouseEnter(self, event):

        await self.bg.setColor(self.style.getColor("hover", self.bg))

    async def onMouseLeave(self, event):

        await self.bg.setColor(self.style.getColor(("select" if self.active else "bg2"), self.bg))

    async def onMouseButtonDown(self, event):

        await self.parent._onSelect(self.entry)

class ListBox(Window):

    """
    A components that shows a list of entries and allows the user to select one.
    """

    def __init__(self, pos, width, height, entries=[], padding=2):

        Window.__init__(self, pos, width, height)


        self.entryHeight = 20
        self.entryPadding = padding

        self._entries = []
        self.createEntries(entries)

    def createEntries(self, entries):

        #cleanup
        for i in self._entries:
            try:
                self.removeObject(i)
            except:
                pass
        self._entries = []

        #create entries
        for i in entries:
            self._addEntrySync(i)

        #Selected entry
        self._selected = None

    def _addEntrySync(self, entry):

        pos = [self.entryPadding, (self.entryHeight+self.entryPadding)*len(self._entries)+self.entryPadding]
        e = _EntryContainer(pos, self.width-self.entryPadding*2, self.entryHeight, entry)
        self.addObject(e)
        self._entries.append(e)

    async def addEntry(self, entry):

        """
        Add a new entry to the listbox and refresh the window.
        """

        self._addEntrySync(entry)
        await self.draw()

    async def removeEntry(self, index):

        """
        Remove the entry at index from the listbox and refresh the window.
        If index is OOB, ValueError will be raised.
        If index is negative, this method is a noop.
        """

        pass

    async def clear(self):

        """
        Remove all entries from this list box.
        """

        for e in self._entries:
            self.removeObject(e)
        self._entries.clear()
        await self.draw()

    async def _onSelect(self, entry):

        for i in self._entries:
            await i.setState(i.entry == entry)

        self._selected = entry

        await self.onSelect(entry)

    async def onSelect(self, entry):

        """
        Select handler.
        This method will be called every time the user selects an entry.
        Subclasses should override this if they wish to implement actions on selection.
        """

        pass

    async def onHover(self, entry):

        """
        Select handler.
        This method will be called every time the user hovers over an entry.
        Subclasses should override this if they wish to implement actions on hovering.
        """

        pass

    def getSelected(self):

        """
        Returns the selected entry.
        Returns None if no entry has been selected yet.
        """

        return self._selected

#CONVENIENCE CLASSES

class TextFieldWithConfirmButton(Window):

    """A convenience frame that will create a TextField with an accompanying confirm Button."""

    pass

class NumberFieldWithConfirmButton(Window):

    """A convenience frame that will create a NumberField with an accompanying confirm Button."""

    pass

class DropDownFieldWithConfirmButton(Window):

    """A convenience frame that will create a DropDownField with an accompanying confirm Button."""

    pass

#DIALOGS

class Dialog(Window):

    """A basic dialog.
    This class will darken the screen and prompt the user with a dialog window, rendering all other parts of the screen inaccessible until the dialog has been closed."""

    def __init__(self, res, width, height, shade=100, bgcolor=[0,0,0], title="Dialog", titleColor=[200,200,200]):

        Window.__init__(self, [0, 0], res[0], res[1])
        self.shade = Background([0, 0], res[0], res[1], [100, 100, 100, shade])
        self.addObject(self.shade)

        self.bg = Background([int(res[0]/2-width/2), int(res[1]/2-height/2)], width, height, bgcolor)
        self.addObject(self.bg)

        #replace standard window manager to add new objects to the background instead of the dialog
        self.addObject = self.addObjectDialog

        self.title = Text([0, 0], title, color=titleColor, size=25)
        self.addObject(self.title)

    def addObjectDialog(self, obj):

        Window.addObject(self.bg, obj)

    async def handleEvent(self, event):

        if self.visible:
            return await self._handleEvent(event)
        return self.visible

class _ButtonDialog(Button):

    def __init__(self, pos, width, label):

        Button.__init__(self, pos, width, 30, label, fontSize=20)

    async def onButtonHit(self, event):

        return await self.parent.parent.handleButtonHit(self.label.text)

class DialogChoice(Dialog):

    """A dialog that prompts the user with a choice of different options."""

    def __init__(self, res, width, height, text="", choices=[], textColor=[200,200,200], **kwargs):

        Dialog.__init__(self, res, width, height, **kwargs)
        self.text = Text([0, 30], text, color = textColor)
        self.addObject(self.text)

        if len(choices) < 1:
            raise ValueError("choices must have at least one element")

        #This object is never added to the window hierarchy, but only used to determine the size of the buttons
        buttonLabelText = Text([0,0], "", size=20)

        sizes = []
        for i in choices:
            sizes.append(buttonLabelText.getTextSize(i)[0]+30)
        total_size = sum(sizes)-10 #delete padding of the last element

        current_offset = int(width/2-total_size/2)
        for i in range(len(choices)):
            button = _ButtonDialog([current_offset, height-35], sizes[i]-10, choices[i])
            self.addObject(button)
            current_offset += sizes[i]

    async def handleButtonHit(self, choice):

        """Override this method to handle button presses by the user."""

        pass

class DialogOK(DialogChoice):

    """A simple dialog that displays some information to the user.
    
    Includes an OK button as well as keyboard shortcuts."""

    def __init__(self, res, width, height, **kwargs):

        DialogChoice.__init__(self, res, width, height, choices=["OK"], **kwargs)

    async def handleButtonHit(self, choice):

        await self.toggleVisibility()

    async def onKeystroke(self, event):

        if event.key == pygame.K_RETURN:
            await self.toggleVisibility()
            return True
        return False

class DialogConfirm(DialogChoice):

    """Like DialogChoice, but the only available choices are Confirm and Cancel."""

    def __init__(self, res, width, height, **kwargs):

        DialogChoice.__init__(self, res, width, height, choices=["Confirm", "Cancel"], **kwargs)

    async def handleButtonHit(self, choice):

        if choice == "Confirm":
            await self.handleConfirm()
        elif choice == "Cancel":
            await self.handleCancel()

    async def handleConfirm(self):

        """Override this method to implement handling for confirm"""

        pass

    async def handleCancel(self):

        """Override this method to implement handling for cancel"""

        pass

class DialogYesNo(DialogChoice):

    """Like DialogChoice, but the only available choices are Yes and No."""

    def __init__(self, res, width, height, **kwargs):

        DialogChoice.__init__(self, res, width, height, choices=["Yes", "No"], **kwargs)

    async def handleButtonHit(self, choice):

        if choice == "Yes":
            await self.handleYes()
        elif choice == "No":
            await self.handleNo()

    async def handleYes(self):

        """Override this method to implement handling for yes"""

        pass

    async def handleNo(self):

        """Override this method to implement handling for no"""

        pass

class DialogOKCancel(DialogChoice):

    """Like DialogChoice, but the only available choices are OK and Cancel."""

    def __init__(self, res, width, height, **kwargs):

        DialogChoice.__init__(self, res, width, height, choices=["OK", "Cancel"], **kwargs)

    async def handleButtonHit(self, choice):

        if choice == "OK":
            await self.handleConfirm()
        elif choice == "Cancel":
            await self.handleCancel()

    async def handleOK(self):

        """Override this method to implement handling for OK"""

        pass

    async def handleCancel(self):

        """Override this method to implement handling for cancel"""

        pass

class DialogWithTextField(DialogOKCancel):

    """A dialog that prompts the user to input some text using a TextField.
    Comes with buttons to confirm or abort the input prompt."""

    pass

class DialogWithNumberField(DialogOKCancel):

    """A dialog that prompts the user to input a number using a NumberField.
    Comes with buttons to confirm or abort the input prompt."""

    pass

#OTHER STUFF

class HorizontalWaveform(Image):

    """
    Draws a pygame.mixer.Sound() or numpy.array containing sound data to the screen as a waveform.
    """

    def __init__(self, pos, width, height, color = [255, 255, 255]):

        Image.__init__(self, pos, pygame.Surface((width, height), pygame.SRCALPHA))

        self.color = color

    async def updateWaveform(self, sound):

        """
        Update the sound view by examining the sound specified. Sound should be of type pygame.mixer.Sound
        or numpy.array. If it is a Sound object, it will be converted into an array using numpy automatically.

        This method aims to be as memory efficient as possible, however, since this is a rather difficult task
        it may be very performance hungry. Try to call it as infrequently as possible.
        """

        #use references to the original sound since we don't want to modify anything
        #(and it is way more memory efficient to do it this way)

        if isinstance(sound, pygame.mixer.Sound):
            a = pygame.sndarray.samples(sound)
        else:
            a = sound

        surf = pygame.Surface((self.width, self.height), flags = pygame.SRCALPHA)

        #now we need to ideally compute the average over all samples that lie in the
        #range of one pixel on screen. The sample offset is 

        #   pixel offset/height * array length

        aWidth = self.width+2
        arrayLength = len(a)

        #our maximum value (in both directions) is going to be half of the available range,
        #depending on the format.
        maxValue = (2**abs(pygame.mixer.get_init()[1]))//4

        for x in range(0, self.width):

            #compute average
            indexStart = x/aWidth*arrayLength
            indexStop = (x+1)/aWidth*arrayLength

            #we need to use absolute values since a waveform has a positive and a negative phase
            average = abs(a[int(indexStart):int(indexStop)]).mean()/maxValue

            #draw the waveform using a rect of width 1
            pygame.draw.rect(surf, self.waveformColor, pygame.Rect(x, self.height/2-(self.height/2)*average, 1, self.height*average))

        #refresh view and redraw
        await self.setImage(surf)
