"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

import sys, traceback, html
from PyQt4 import QtCore, QtGui


class WMainWindow(QtGui.QMainWindow):

    _windowIcon = ':/icons/fugue/leaf-plant.png'
    _windowTitle = 'wic'
    _authenticationEnabled = True
    _unconditionalQuit = True # whether to allow unconditional quit (if some forms didn't close)

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle(self._windowTitle)
        self.setWindowIcon(QtGui.QIcon(self._windowIcon))

        mdiArea = QtGui.QMdiArea()
        mdiArea.setDocumentMode(True)
        mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mdiArea.setViewMode(mdiArea.TabbedView)
        mdiArea.setTabPosition(QtGui.QTabWidget.North)
        mdiArea.setActivationOrder(mdiArea.ActivationHistoryOrder)
        mdiArea.subWindowActivated.connect(self.onSubwindowActivated)
        self.setCentralWidget(mdiArea)
        self.mdiArea = mdiArea

        tabBar = mdiArea.findChildren(QtGui.QTabBar)[0] # hack: http://www.qtforum.org/article/31711/close-button-on-tabs-of-mdi-windows-qmdiarea-qmdisubwindow-workaround.html
        tabBar.setTabsClosable(True)
        tabBar.setExpanding(False)
        tabBar.setMovable(True)
        tabBar.setDrawBase(True)
        #tabBar.setShape(tabBar.TriangularSouth)
        #tabBar.setIconSize(QtCore.QSize(16, 16))
        self.tabBar = tabBar

        tabBarEventFilter = TabBarEventFilter(self)
        tabBar.installEventFilter(tabBarEventFilter)

        self.statusBar() # create status bar

        from wic.messages_window import MessagesWindow
        self.messagesWindow = MessagesWindow(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.messagesWindow)

        self.printMessage = self.messagesWindow.printMessage # not nice

        sys.stdout = MessagesOut(self.printMessage)  # hook the real STDOUT
        sys.excepthook = exception_hook # set our exception hook


        from wic import w_settings
        self.settings = w_settings.WSettings(self)

        self.setupMenu()

        if self._authenticationEnabled:
            self.authenticate()
        QtCore.QTimer.singleShot(0, self.onSystemStarted) # when event loop is working

    def setupMenu(self):
        from wic import menus
        self.menu = menus.MainMenu(self)

    def onSubwindowActivated(self, subWindow): # http://doc.trolltech.com/latest/qmdiarea.html#subWindowActivated
        #self.mdiArea.setActiveSubWindow(subWindow)
        saveActive = bool(subWindow and subWindow.isWindowModified())
        #self.fileSaveAction.setEnabled(saveActive)

    def onTabBarLeftDblClick(self):
        subWindow = self.mdiArea.currentSubWindow()
        if subWindow.isMaximized():
            subWindow.showNormal()
        else:
            subWindow.showMaximized()

    def closeEvent(self, event):
        self.mdiArea.closeAllSubWindows() # Passes a close event from main window to all subwindows.
        if self.mdiArea.subWindowList(): # there are still open subwindows
            event.ignore()
            return
        if self.onSystemAboutToQuit() is False: # именно False, иначе None тоже считается отрицательным
            event.ignore()
            return
        self.settings.saveSettings()

    def restoreSubwindows(self):
        for window in self.mdiArea.subWindowList():
            window.showNormal()

    def minimizeSubwindows(self):
        for window in self.mdiArea.subWindowList():
            window.showMinimized()

    def addSubWindow(self, widget): # https://bugreports.qt.nokia.com/browse/QTBUG-9462
        """Add a new subwindow with the given widget
        """
        subWindow = QtGui.QMdiSubWindow() # no parent
        subWindow.setWidget(widget)
        subWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.mdiArea.addSubWindow(subWindow)
        subWindow.setWindowIcon(widget.windowIcon())
        subWindow.show()
        from wic import forms
        if isinstance(widget, forms.WForm):
            widget.closed.connect(subWindow.close) # when form closes - close subWindow too
        return subWindow

    def authenticate(self):
        """Show log in window."""

    def requestQuit(self, unconditional = False):
        """Request application quit."""
        #self._unconditionalQuit = unconditional
        self.close() # TODO: check for self._unconditionalQuit when closing forms and mainWindow

    def onSystemStarted(self):
        """Called on startup when everything is ready."""

    def onSystemAboutToQuit(self):
        """Called when the app is requested to quit. Return False to cancel"""

    def showWarning(self, title, text):
        """Convenience function to show a warning message box."""
        QtGui.QMessageBox.warning(self, title, text)

    def showInformation(self, title, text):
        """Convenience function to show an information message box."""
        QtGui.QMessageBox.information(self, title, text)



class TabBarEventFilter(QtCore.QObject):
    """Event filter for main window's tab bar.
    """
    def eventFilter(self, tabBar, event):
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() == QtCore.Qt.LeftButton:
                self.parent().onTabBarLeftDblClick()
                return True # message processed
        return super().eventFilter(tabBar, event) # standard event processing        


def exception_hook(excType, excValue, excTraceback): 
    """Global function to catch unhandled exceptions (mostly in user modules).
    """
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
    """Our replacement for stdout. It prints messages also the the messages window. 
    If txt does not start with '<>' it is escaped to be properly shown in QTextEdit.
    """

    def __init__(self, printMessageFunc):
        self.printMessage = printMessageFunc

    def write(self, txt):
        print(txt, end = '', file = sys.__stdout__)
        if not txt.startswith('<>'):
            txt = html.escape(txt)
        self.printMessage(txt, end = '')

    def flush(self):
        sys.__stdout__.flush()
