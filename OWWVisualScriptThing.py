import os
import sys
import asyncio
import logging

import pygame
import window
from window.window import setLayoutDebugMode, EVENT_APP_STARTED

import ui
import graph

logging.basicConfig(level=logging.DEBUG)

pygame.init()

loop = asyncio.get_event_loop()

#setLayoutDebugMode(True)

App = window.ApplicationHandle(loop=loop)
App.setDisplayFlags(pygame.NOFRAME)
App.setDisplayFlags(window.SDLFlags.CENTER_WINDOW, "1")
App.setDisplayCaption("Overwatch Visual Scripting Editor - Untitled")

root = App.getRoot()

GRAPH = graph.Graph()

windowBar = ui.WindowBar(App.size)
root.addObject(windowBar)
menuBar = ui.MenuBar(App.size)
root.addObject(menuBar)
graphViewer = ui.GraphViewer(App.size, GRAPH)
root.addObject(graphViewer)
blockDrawer = ui.BlockDrawer(App.size)
root.addObject(blockDrawer)
dnd = ui.DnDLayer(App.size)
root.addObject(dnd)

async def handleUserEvent(event):

    if event.name == "quit":
        App.stop()
        return True
    elif event.name == "newRule":
        logging.debug("New rule was triggered")
        await graphViewer.createNewBlock(graph.BlockType.RULE, {}, dnd)
    elif event.name == "newBlock":
        logging.debug("newBlock was triggered")
        await graphViewer.createNewBlock(event._type, event.entry, dnd)
    elif event.name == "newCondition":
        logging.debug("newCondition was triggered")
        await graphViewer.createNewBlock(graph.BlockType.CONDITION, {}, dnd)
    elif event.name == "export":
        pygame.scrap.put(pygame.SCRAP_TEXT, GRAPH.compile().encode())

async def initScrap(event):

    logging.debug("initializing scrap...")
    pygame.scrap.init()

App.registerEventHandle(window.EventHandle(pygame.USEREVENT, {}, handleUserEvent))
App.registerEventHandle(window.EventHandle(EVENT_APP_STARTED, {}, initScrap))

App.start()
loop.run_forever()