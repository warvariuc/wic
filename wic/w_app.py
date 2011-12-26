import sys
import traceback

from PyQt4 import QtCore, QtGui

import wic


class WApp(QtGui.QApplication):

    def __init__(self, argv):
        if wic.app:
            raise Exception('There can be only one WApp instance')

        super().__init__(argv)
        self.setup()

        QtCore.QTimer.singleShot(0, self.onSystemStarted) # when event loop is working
        wic.app = self

    def setup(self):
        self.setWindowIcon(QtGui.QIcon(':/icons/fugue/leaf-plant.png'))
        self.setOrganizationName('vic')
        self.setApplicationName('wic')

        from wic import main_window

        self.mainWindow = main_window.WMainWindow()
        self.statusBar = self.mainWindow.statusBar()
        self.messagesWindow = self.mainWindow.messagesWindow
        self.printMessage = self.messagesWindow.printMessage

        sys.stdout = MessagesOut(self.printMessage)  # redirect the real STDOUT
        sys.excepthook = exception_hook # set our exception hook

        self.mainWindow.show() # show main wndow


    def onSystemStarted(self):
        """Called when everything is ready"""

    def onSystemAboutToExit(self):
        """предопределенная процедура запускаемая при завершении работы системы"""

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


class MessagesOut():
    """Our replacement for stdout. It prints messages also the the messages window."""
    def __init__(self, printMessage):
        self.printMessage = printMessage

    def write(self, txt):
        print(txt, end = '', file = sys.__stdout__)
        self.printMessage(txt, end = '')
    def flush(self):
        sys.__stdout__.flush()

