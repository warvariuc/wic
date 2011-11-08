import sys, os, importlib
from PyQt4 import QtCore, QtGui


try: # monkeypatch: use cdecimal if present instead of decimal = it is faster
    import cdecimal
    sys.modules['decimal'] = cdecimal 
except ImportError: 
    pass

import wic
from wic import w_app, w_main_window


def exception_hook(excType, excValue, excTraceback): # Global function to catch unhandled exceptions (mostly in user modules)
    import traceback
    info = ''.join(traceback.format_exception(excType, excValue, excTraceback))
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

    wic.mainWindow.messagesWindow.printMessage(info)

sys.excepthook = exception_hook # set our exception hook




app = wic.app = w_app.WApp(sys.argv)
appDir = QtGui.qApp.appDir = os.path.dirname(os.path.abspath(__file__))


mainWindow = wic.mainWindow = QtGui.qApp.mainWindow = w_main_window.WMainWindow()
mainWindow.show()
wic.messagesWindow = mainWindow.messagesWindow
from wic import orm
wic.db = orm.SqliteAdapter('sqlite://../../mtc.sqlite')


# load default test configuration
import conf
QtCore.QTimer.singleShot(0, conf.on_SystemStart) # когда начнет работать очередь сообщений - загрузить тестовую конфигурацию

app.exec() # start the event loop
