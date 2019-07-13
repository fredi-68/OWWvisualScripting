import asyncio

import pygame
import pygame.gfxdraw

from window import Window
from window.window import postEvent
from window.components import Background, Image, VerticalGradient, Text
from window.ui import Button, ListBox, TextField, NumberField, DropDownField

from graph import *

def brighter(color, amount=10):

    """
    Brighten a color
    """

    return list(map(lambda x: min(x+amount, 255), color))

class ButtonClose(Button):

    def __init__(self, pos, width, height):

        bgColor = (255, 10, 10)
        bgHoverColor = (255, 100, 100)
        checkmarkColor = (255, 255, 255)

        fieldPadding = 4
        lineMult = 0.2
        hOffset = width/2-height/2

        fieldBg = pygame.Surface((width, height))
        fieldBg.fill(bgColor)

        fieldHoverBg = pygame.Surface((width, height))
        fieldHoverBg.fill(bgHoverColor)

        pygame.draw.line(fieldBg, checkmarkColor, [fieldPadding+hOffset, fieldPadding], [height-fieldPadding+hOffset, height-fieldPadding], int(height*lineMult))
        pygame.draw.line(fieldBg, checkmarkColor, [fieldPadding+hOffset, height-fieldPadding], [height-fieldPadding+hOffset, fieldPadding], int(height*lineMult))

        pygame.draw.line(fieldHoverBg, checkmarkColor, [fieldPadding+hOffset, fieldPadding], [height-fieldPadding+hOffset, height-fieldPadding], int(height*lineMult))
        pygame.draw.line(fieldHoverBg, checkmarkColor, [fieldPadding+hOffset, height-fieldPadding], [height-fieldPadding+hOffset, fieldPadding], int(height*lineMult))

        Button.__init__(self, pos, width, height, image=fieldBg, hoverImage=fieldHoverBg, clickImage=fieldBg)

    async def onButtonHit(self, event):

        postEvent(pygame.USEREVENT, {"name":"quit"})

class WindowBar(Window):

    def __init__(self, res):

        Window.__init__(self, [0, 0], res[0], 30)
        self.bg = VerticalGradient([0, 0], self.width, self.height, (255, 255, 255), (120, 120, 120))
        self.addObject(self.bg)

        self.icon = Image([3, 3], pygame.image.load("res/icon.png"))
        self.addObject(self.icon)
        self.title = Text([34, 3], "Overwatch Visual Scripting Editor - Untitled", size=28, color=(0, 0, 0))
        self.addObject(self.title)

        self.buttonClose = ButtonClose([self.width - 65, 4], 50, 20)
        self.addObject(self.buttonClose)

class ButtonNewRule(Button):

    def __init__(self, pos):

        super().__init__(pos, 80, 30, "New Rule", fontSize=25, bgColor=[0, 100, 0], bgHoverColor=[60, 160, 60])

    async def onButtonHit(self, event):

        postEvent(pygame.USEREVENT, {"name": "newRule"})

class ButtonNewCondition(Button):

    def __init__(self, pos):

        super().__init__(pos, 140, 30, "New Condition", fontSize=25, bgColor=[200, 150, 0])

    async def onButtonHit(self, event):

        postEvent(pygame.USEREVENT, {"name": "newCondition"})

class ButtonExport(Button):

    def __init__(self, pos):

        super().__init__(pos, 200, 30, "Export to Clipboard", fontSize=25, bgColor=[150, 150, 230])

    async def onButtonHit(self, event):

        postEvent(pygame.USEREVENT, {"name": "export"})

class MenuBar(Window):

    def __init__(self, res):

        Window.__init__(self, [0, 30], res[0], 40)
        self.bg = VerticalGradient([0, 0], self.width, self.height, (200, 200, 200), (120, 120, 120))
        self.addObject(self.bg)
        self.buttonNewRule = ButtonNewRule([3, 3])
        self.addObject(self.buttonNewRule)
        self.buttonNewCondition = ButtonNewCondition([100, 3])
        self.addObject(self.buttonNewCondition)
        self.buttonExport = ButtonExport([250, 3])
        self.addObject(self.buttonExport)

class BlockWrapperSocket(Window):

    SOCKET_BG = (50, 50, 50)

    def __init__(self, pos, type, socket, color, size, margin):

        super().__init__(pos, size, size)
        self.type = type
        self.socket = socket
        self.addObject(Background([0, 0], size, size, self.SOCKET_BG))
        self.addObject(Background([margin, margin], size-margin*2, size-margin*2, color))

    async def onMouseButtonDown(self, event):

        if self.type == "output":
            if event.button == 1:
                #Start drawing line
                self.logger.debug("start drawing line from %s" % str(self.socket))
                await self.parent.parent.startDrawing(self)
                return True

    async def onMouseButtonUp(self, event):

        if self.type == "input":
            if event.button == 1:
                #Stop drawing line
                self.logger.debug("finish drawing line to %s" % str(self.socket))
                await self.parent.parent.stopDrawing(self)
                return True

class BlockWrapperHeader(Window):

    def __init__(self, text, color):

        self.text = Text([10, 0], text, size=30)
        super().__init__([0, 0], self.text.width, self.text.height)
        self.addObject(self.text)
        self.bg = Background([0, 0], self.width+20, self.height, color)
        self.addObject(self.bg)
        self.addObject(self.text)

    async def onMouseButtonDown(self, event):

        if event.button == 1:
            await self.parent.startFocusing()
            return True

class _NumField(NumberField):

    def __init__(self, pos, width, param):

        super().__init__(pos, width, 25, defaultText=str(param.value))
        self.param = param

    async def onKeystroke(self, event):

        await super().onKeystroke(event)
        try:
            self.param.value = float(self.getText())
        except:
            pass

class _TextField(TextField):

    def __init__(self, pos, width, param):

        super().__init__(pos, width, 25, defaultText=str(param.value))
        self.param = param

    async def onKeystroke(self, event):

        await super().onKeystroke(event)
        self.param.value = self.getText()

class _DropDown(DropDownField):

    def __init__(self, pos, width, param):

        super().__init__(pos, width, 25, param.values, default=param.value)
        self.param = param

    async def onValueChange(self, value):

        self.param.value = value

class BlockWrapper(Window):

    """
    Displays an action or value block.
    """

    COLORS = {
        "action": (239, 131, 84),
        "value": (238, 75, 106),
        "rule": (170, 73, 170),
        "condition": (80, 151, 153)
        }

    PARAM_CLASSES = {
        ParameterType.DROP_DOWN: _DropDown,
        ParameterType.NUMBER_FIELD: _NumField,
        ParameterType.TEXT_FIELD: _TextField
        }

    SOCKET_BG = (50, 50, 50)
    BOX_BG = (100, 100, 100)

    SOCKET_SIZE = 18
    SOCKET_MARGIN = 2
    SOCKET_PADDING = 5

    def __init__(self, pos, block):

        self.header = BlockWrapperHeader(block.name, self.COLORS[block.TYPE.value])
        width = self.header.width + 20
        s_height = self.SOCKET_PADDING * 2 + self.SOCKET_SIZE
        param_offset = 50 * len(block.parameters)
        height = 30 + (len(block.inputs) + len(block.outputs)) * s_height + param_offset

        self.block = block
        _elements = []

        #Draw parameters
        i = 0
        for param in block.parameters:
            y = 30 + i * 50
            label = Text([2, y], param.name, size=24)
            _elements.append(label)
            ctrl = self.PARAM_CLASSES[param.type]([2, y+25], width-4, param)
            _elements.append(ctrl)
            i += 1

        #Draw inputs and outputs
        sock_width = self.SOCKET_SIZE - self.SOCKET_MARGIN * 2
        inputs = list(block.inputs.values())
        self.inputs = []
        for i in range(len(inputs)):
            y = 30 + s_height * i + self.SOCKET_PADDING + param_offset
            input = inputs[i]
            socket = BlockWrapperSocket([0, y], "input", input, self.COLORS[input.type.value], self.SOCKET_SIZE, self.SOCKET_MARGIN)
            _elements.append(socket)
            text = Text([self.SOCKET_SIZE + self.SOCKET_PADDING, y], input.name, size=20)
            _elements.append(text)
            self.inputs.append(socket)

        outputs = list(block.outputs.values())
        self.outputs = []
        for i in range(len(outputs)):
            y = 30 + s_height * (i + len(inputs)) + self.SOCKET_PADDING + param_offset
            output = outputs[i]
            color = self.COLORS[output.type.value]
            socket = BlockWrapperSocket([width-self.SOCKET_SIZE, y], "output", output, self.COLORS[output.type.value], self.SOCKET_SIZE, self.SOCKET_MARGIN)
            _elements.append(socket)
            text = Text([self.SOCKET_PADDING, y], output.name, size=20)
            _elements.append(text)
            self.outputs.append(socket)

        #width = max(map(lambda x: x.width, _elements))
        super().__init__(pos, width, height)

        #Draw bg and header
        self.bg = Background([0, 0], self.width, self.height, brighter(self.COLORS[block.TYPE.value], 50))
        self.addObject(self.bg)
        self.addObject(self.header)

        for i in _elements:
            self.addObject(i)

    async def startFocusing(self):

        await self.parent.dnd.startFocusing(self, self.parent)

class BlockDrawerEntry(Window):

    COLORS = {
        "action": (239, 131, 84),
        "value": (238, 75, 106),
        "rule": (170, 73, 170),
        "condition": (80, 151, 153)
        }

    def __init__(self, pos, width, height, entry, type):

        super().__init__(pos, width, height)
        self.entry = entry
        self.type = type
        self.orgpos = pos[:]

        self.bg = Background([0, 0], width, height, self.COLORS[type.value])
        self.addObject(self.bg)
        self.title = Text([3, 3], entry["name"], size=20)
        self.addObject(self.title)

    def scroll(self, offset):

        self.pos = [self.pos[0], self.orgpos[1] + offset]

    async def onMouseButtonDown(self, event):

        if event.button == 1:
            postEvent(pygame.USEREVENT, {"name": "newBlock", "_type": self.type, "entry": self.entry})
            return True

class BlockDrawerCont(Window):

    SCROLL_SPEED = 60
    ENTRY_HEIGHT = 50
    ENTRY_PADDING = 5

    def __init__(self, pos, width, height):

        super().__init__(pos, width, height)
        self.scroll_offset = 0

        self._entries = []

    def createBlockList(self, wsjson):

        for i in self._entries:
            self.removeObject(i)
        self._entries = []
        self._lastIndex = 0
        self.scroll_offset = 0

        for action in wsjson["actions"]:
            #fuck this
            entry = BlockDrawerEntry([
                self.ENTRY_PADDING,
                self._lastIndex * (self.ENTRY_HEIGHT + self.ENTRY_PADDING * 2) + self.ENTRY_PADDING
                ], self.width - self.ENTRY_PADDING * 2, self.ENTRY_HEIGHT, action, BlockType.ACTION)
            self._entries.append(entry)
            self.addObject(entry)
            self._lastIndex += 1

        for value in wsjson["values"]:
            #fuck this
            entry = BlockDrawerEntry([
                self.ENTRY_PADDING,
                self._lastIndex * (self.ENTRY_HEIGHT + self.ENTRY_PADDING * 2) + self.ENTRY_PADDING
                ], self.width - self.ENTRY_PADDING * 2, self.ENTRY_HEIGHT, value, BlockType.VALUE)
            self._entries.append(entry)
            self.addObject(entry)
            self._lastIndex += 1

    async def onMouseButtonDown(self, event):

        if event.button == 5:
            self.scroll_offset -= self.SCROLL_SPEED
            await self.scroll()
            return True

        elif event.button == 4:
            self.scroll_offset += self.SCROLL_SPEED
            if self.scroll_offset > 0:
                self.scroll_offset = 0
            await self.scroll()
            return True

    async def scroll(self):

        for i in self._entries:
            i.scroll(self.scroll_offset)
        await self.draw()

class BlockDrawer(Window):

    WIDTH = 300
    HEADER_SIZE = 60

    def __init__(self, res):

        super().__init__([res[0]-self.WIDTH, 70], self.WIDTH, res[1]-70)
        self.bg = Background([0, 0], self.width, self.height, (100, 100, 100))
        self.addObject(self.bg)

        self.container = BlockDrawerCont([0, self.HEADER_SIZE], self.width, self.height-self.HEADER_SIZE)
        self.addObject(self.container)

        self.search_label = Text([5, 5], "Search:", size=25, color=(200, 200, 200))
        self.addObject(self.search_label)
        self.search_entry = TextField([5, 30], self.width-10, 25)
        self.addObject(self.search_entry)

        self.wsjson = loadWorkshopJSON()
        self.container.createBlockList(self.wsjson)

    def filter(self, search):

        if not search:
            return self.wsjson

        actions = []
        for action in self.wsjson["actions"]:
            if search in action["name"].lower():
                actions.append(action)

        values = []
        for value in self.wsjson["values"]:
            if search in value["name"].lower():
                values.append(value)

        return {"actions": actions, "values": values}

    async def onKeystroke(self, event):

        if event.key == pygame.K_RETURN:
            text = self.search_entry.getText()
            await self.search_entry.text.setText("")
            self.container.createBlockList(self.filter(text))
            await self.container.draw()

class GraphViewer(Window):

    LINE_COLOR = (200, 200, 200)
    LINE_SIZE = 3
    LINE_SMOOTH = 10

    #line style: 0 = linear, 1 = bezier curve
    LINE_STYLE = 1

    def __init__(self, res, g):

        super().__init__([0, 70], res[0] - 300, res[1] - 70)
        self.bg = Background([0, 0], self.width, self.height, (50, 50, 50))
        self.addObject(self.bg)
        self.blocks = []
        self.scrollPos = [0, 0]
        self.isScrolling = False
        self.currentLineStart = [0, 0]
        self.isDrawing = False
        self.currentOutput = None
        self.graph = g
        self.dnd = None
        self.lineLayer = Image([0, 0], self._createLineSurf())
        self.addObject(self.lineLayer)

    async def createNewBlock(self, type, data, dnd):

        self.dnd = dnd
        if type == BlockType.RULE:
            self.logger.debug("Creating new rule block...")
            block = RuleBlock("New Rule", EventType.GLOBAL)
            wrap = BlockWrapper([50, 50], block)
            self.graph.addBlock(block)
            await dnd.startFocusing(wrap, self)
        elif type == BlockType.ACTION:
            self.logger.debug("Creating new action block...")
            block = ActionBlock.fromJSON(data)
            wrap = BlockWrapper(pygame.mouse.get_pos(), block)
            await dnd.startFocusing(wrap, self)
        elif type == BlockType.VALUE:
            self.logger.debug("Creating new value block...")
            block = ValueBlock.fromJSON(data)
            wrap = BlockWrapper(pygame.mouse.get_pos(), block)
            await dnd.startFocusing(wrap, self)
        elif type == BlockType.CONDITION:
            self.logger.debug("Creating new condition block...")
            block = ConditionBlock()
            wrap = BlockWrapper(pygame.mouse.get_pos(), block)
            await dnd.startFocusing(wrap, self)

    def addObject(self, obj):

        super().addObject(obj)
        if isinstance(obj, BlockWrapper):
            if obj not in self.blocks:
                self.blocks.append(obj)
            loop = asyncio.get_event_loop()
            loop.create_task(self.redrawLines())

    async def startDrawing(self, socket):

        if self.isDrawing:
            return
        self.isDrawing = True
        self.currentLineStart = self.posGlobalToLocal(socket.parent.posLocalToGlobal(socket.center))
        self.currentOutput = socket.socket

    async def stopDrawing(self, socket):

        if not self.isDrawing:
            return
        self.isDrawing = False
        self.currentLine = None
        output = self.currentOutput
        input = socket.socket
        input.block.connectInput(input, output, output.block)
        await self.redrawLines()

    def _drawLine(self, surf, p_from, p_to):

        #TODO: make bezier curves thicker
        if self.LINE_STYLE:
            width = abs(p_from[0] - p_to[0])//2
            points = [
                p_from,
                [p_from[0] + width, p_from[1]],
                [p_to[0] - width, p_to[1]],
                p_to
                ]
        
            pygame.gfxdraw.bezier(surf, points, self.LINE_SMOOTH, self.LINE_COLOR)
        else:
            pygame.draw.line(surf, self.LINE_COLOR, p_from, p_to, self.LINE_SIZE)

    def _createLineSurf(self):

        surf = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        
        outputs = {}

        for block in self.blocks:
            for output in block.outputs:
                outputs[output.socket] = output

        for block in self.blocks:
            #iterate over inputs to find all existing connections
            for input in block.inputs:
                dest = self.posGlobalToLocal(block.posLocalToGlobal(input.center))
                for output in input.socket.targets:
                    b = outputs[output]
                    src = self.posGlobalToLocal(b.parent.posLocalToGlobal(b.center))
                    self._drawLine(surf, src, dest)

        return surf

    async def redrawLines(self):

        await self.lineLayer.setImage(self._createLineSurf())

    async def onMouseMotion(self, event):

        pass

    async def deleteBlock(self, block):

        pass

class DnDLayer(Window):

    def __init__(self, res):

        super().__init__([0, 0], *res)
        self.element = None
        self.isFocusing = False
        self.target = None

    async def startFocusing(self, element, target):

        if element.parent:
            pos = target.posLocalToGlobal(element.pos)
            element.parent.removeObject(element)
        else:
            pos = element.pos

        self.element = element
        self.target = target
        self.addObject(element)
        element.pos = self.posGlobalToLocal(pos)
        self.isFocusing = True
        await self.draw()

    async def onMouseMotion(self, event):

        if self.isFocusing:
            await self.element.setPos(event.pos)
            return True

    async def onMouseButtonUp(self, event):

        if self.isFocusing:
            if event.button == 1:
                if self.target.pointInWindow(event.pos):
                    self.isFocusing = False
                    self.removeObject(self.element)
                    self.element.pos = self.target.posGlobalToLocal(self.posLocalToGlobal(self.element.pos))
                    self.target.addObject(self.element)
                    await self.element.draw()
                    self.target = None
                    self.element = None
                else:
                    self.removeObject(self.element)
                    await self.draw()
                    self.isFocusing = False
                    self.target = None
                    self.element = None

            return True

