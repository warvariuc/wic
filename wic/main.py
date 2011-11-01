#!/usr/bin/env python3

'''wic (vix, wix?) platform'''

import sys, os
from PyQt4 import QtCore, QtGui

# monkeypatch: use cdecimal if present instead of decimal = it is much faster
try: 
    #sys.modules['decimal'] = __import__('cdecimal') # http://www.bytereef.org/libmpdec-download.html
    import cdecimal
except ImportError: 
    pass
else:
    sys.modules['decimal'] = cdecimal

import wic.widgets.w_widgets_rc # load resources (icons, etc.)
from wic import w_app, w_main_window

app = w_app.WApp(sys.argv)
appDir = QtGui.qApp.appDir = os.path.dirname(os.path.abspath(__file__))


mainWindow = QtGui.qApp.mainWindow = w_main_window.WMainWindow()
mainWindow.show()


def exception_hook(excType, excValue, excTraceback): # Global function to catch unhandled exceptions (mostly in user modules)
    import traceback
    info = ''.join (traceback.format_exception(excType, excValue, excTraceback))
    print(info)
#    import inspect
#    records = inspect.getinnerframes(exc_traceback) # http://docs.python.org/dev/library/inspect.html#inspect.getinnerframes
#    info = '<b>Произошло исключение</b>. История вызовов:\n'
#    for frame, file, lnum, func, lines, index in records:
#        info = info + '&nbsp;&nbsp;' \
#            'Файл "<span style="background-color:#EDEFF4"> ' + file + ' </span>", ' \
#            'строка <span style="background-color:#EDEFF4">&nbsp;' + str(lnum) + ' </span>, ' \
#            'функция <span style="background-color:#EDEFF4">&nbsp;' + func + ' </span>' \
#            '\n&nbsp;<span style="color:maroon">&nbsp;' + lines[0] + ' </span>'
#    info = info + '<br>Описание ошибки: <span style="background-color:#EDEFF4">&nbsp;' + exc_type.__name__ + ' </span>: ' \
#        '<span style="color:maroon">&nbsp;' + str(exc_value).replace('\n', '\n&nbsp;') + '</span>'

    QtGui.qApp.mainWindow.messagesWindow.printMessage(info)

sys.excepthook = exception_hook # set our exception hook


def loadTestConf(): # load default test configuration
    from wic import w
    w.loadConf(os.path.join(QtGui.qApp.appDir, '..', 'conf/'))

QtCore.QTimer.singleShot(0, loadTestConf) # когда начнет работать очередь сообщений - загрузить тестовую конфигурацию

app.exec() # start the event loop
