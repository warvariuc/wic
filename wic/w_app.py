import sys
import traceback

from PyQt4 import QtCore, QtGui

import wic


class WApp(QtGui.QApplication):
    
    _authenticationEnabled = True
    _unconditionalQuit = True # whether to allow unconditional quit (if some forms didn't close)
    _windowIcon = ':/icons/fugue/leaf-plant.png'
    _organizationName = 'vic'
    _applicationName = 'wic'

    def __init__(self, argv):
        if wic.app:
            raise Exception('There can be only one WApp instance')

        super().__init__(argv)
        self.setup()
        if self._authenticationEnabled:
            self.authenticate()

        QtCore.QTimer.singleShot(0, self.onSystemStarted) # when event loop is working
        wic.app = self

    def setup(self):
        self.setWindowIcon(QtGui.QIcon(self._windowIcon))
        self.setOrganizationName(self._organizationName)
        self.setApplicationName(self._applicationName)

        from wic import main_window

        self.mainWindow = main_window.WMainWindow()
        self.statusBar = self.mainWindow.statusBar()
        self.messagesWindow = self.mainWindow.messagesWindow
        self.printMessage = self.messagesWindow.printMessage
        self.menu = self.mainWindow.menu

        sys.stdout = MessagesOut(self.printMessage)  # hook the real STDOUT
        sys.excepthook = exception_hook # set our exception hook

        self.mainWindow.show() # show main wndow

    def authenticate(self):
        """Show log in window."""

    def requestQuit(self, unconditional=False):
        """Request application quit."""
        self._unconditionalQuit = unconditional
        self.mainWindow.close() # TODO: check wic.app._unconditionalQuit when closing forms and mainWindow

    def onSystemStarted(self):
        """Called when everything is ready"""

    def onSystemAboutToQuit(self):
        """Called when app is requested to quit. Return False to cancel"""

    def showWarning(self, title, text):
        QtGui.QMessageBox.warning(self.mainWindow, title, text)

    def showInformation(self, title, text):
        QtGui.QMessageBox.information(self, self.mainWindow, title, text)



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


import html

class MessagesOut():
    """Our replacement for stdout. It prints messages also the the messages window. 
    If txt does not start with '<>' it is escaped to be properly shown in QTextEdit."""

    def __init__(self, printMessage):
        self.printMessage = printMessage

    def write(self, txt):
        print(txt, end='', file=sys.__stdout__)
        if not txt.startswith('<>'):
            txt = html.escape(txt)
        self.printMessage(txt, end='')
    def flush(self):
        sys.__stdout__.flush()
