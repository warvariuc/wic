"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import sys, os

pythonRequiredVersion = '3.2'
if sys.version < pythonRequiredVersion:
    sys.exit('Python %s or newer required (you are using: %s).' % (pythonRequiredVersion, sys.version))

try:
    from wic.widgets import w_widgets_rc # load resources (icons, etc.)
except ImportError:
    sys.exit('Looks like resources are not compiled. Please run `compile_resources.py`.')

try: # monkeypatch: use cdecimal instead of decimal, if present - it is faster
    import cdecimal
    sys.modules['decimal'] = cdecimal
except ImportError:
    pass

appDir = os.path.dirname(os.path.abspath(__file__))



class Bunch(): # Alex Martelli's recipe
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)



if hasattr(sys, 'argv'): # for qt designer

    from wic import app, main_window

    app = app.WApp(sys.argv)
    mainWindow = main_window.WMainWindow()
    statusBar = mainWindow.statusBar()
    messagesWindow = mainWindow.messagesWindow
    printMessage = messagesWindow.printMessage


    class MessagesOut():
        """Our replacement for stdout. It prints messages also the the messages window."""
        def write(self, txt):
            print(txt, end = '', file = sys.__stdout__)
            printMessage(txt, end = '')
        def flush(self):
            sys.__stdout__.flush()

    sys.stdout = MessagesOut()  # redirect the real STDOUT


    from PyQt4 import QtGui

    def showWarning(title, text):
        QtGui.QMessageBox.warning(mainWindow, title, text)
    def showInformation(title, text):
        QtGui.QMessageBox.information(mainWindow, title, text)


    import traceback

    def exception_hook(excType, excValue, excTraceback): # Global function to catch unhandled exceptions (mostly in user modules)
        #traceback.print_exc()
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

        #mainWindow.messagesWindow.printMessage(info)

    sys.excepthook = exception_hook # set our exception hook
