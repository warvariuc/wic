#!/usr/bin/env python3

from PyQt4 import QtCore
import wic, conf


# load  configuration, when event loop is working
QtCore.QTimer.singleShot(0, conf.on_systemStarted)

wic.mainWindow.show() # show main wndow
wic.app.exec() # start the event loop
