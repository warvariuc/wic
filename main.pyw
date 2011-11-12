#!/usr/bin/env python3

from PyQt4 import QtCore
import wic, conf


# load  configuration
QtCore.QTimer.singleShot(0, conf.on_systemStart) # когда начнет работать очередь сообщений - загрузить тестовую конфигурацию
wic.app.exec() # start the event loop
    
