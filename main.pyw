#!/usr/bin/env python3

'''wic (vix, wix?) platform'''

import sys

if sys.hexversion < 0x03010000:
    print("At least Python 3.1 needed. Exiting.");
    sys.exit(1) 


# monkeypatch: use cdecimal if present instead of decimal = it is much faster
try: sys.modules['decimal'] = __import__('cdecimal') # http://www.bytereef.org/libmpdec-download.html
except ImportError: pass


import os
from PyQt4 import QtCore, QtGui


app = __import__('w_app').WApp(sys.argv)

QtGui.qApp.appDir = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(os.path.join(QtGui.qApp.appDir, 'widgets')) # path for searching resources and custom widgets modules
__import__('w_widgets_rc') # load icons and possibly other resources


import w_main_window
QtGui.qApp.mainWindow = w_main_window.WMainWindow()
QtGui.qApp.mainWindow.show()

def exception_hook(exc_type, exc_value, exc_traceback): # Global function to catch unhandled exceptions (mostly in user modules)
    import traceback
    info = ''.join (traceback.format_exception(exc_type, exc_value, exc_traceback))
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
    
sys.excepthook = exception_hook


def loadTestConf(): # load default test configuration
    __import__('w').loadConf(os.path.join(QtGui.qApp.appDir, 'conf/'))
    
QtCore.QTimer.singleShot(0, loadTestConf) # когда начнет работать очередь сообщений - загрузить тестовую конфигурацию

res = app.exec() # start the event loop
sys.exit(res)

