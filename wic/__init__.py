import sys, os

if sys.hexversion < 0x03010000:
    sys.exit("Python 3.1 or newer required.")

appDir = os.path.dirname(os.path.abspath(__file__))

try: # monkeypatch: use cdecimal if present instead of decimal = it is faster
    import cdecimal
    sys.modules['decimal'] = cdecimal 
except ImportError: 
    pass

from PyQt4 import QtGui
from .widgets import w_widgets_rc # load resources (icons, etc.)
from wic import w_app, w_main_window

app = w_app.WApp(sys.argv)

mainWindow = QtGui.qApp.mainWindow = w_main_window.WMainWindow()
messagesWindow = mainWindow.messagesWindow

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

    mainWindow.messagesWindow.printMessage(info)

sys.excepthook = exception_hook # set our exception hook

mainWindow.show()
#wic.app.exec() # start the event loop
