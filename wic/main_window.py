import sys, traceback, html

from PyQt5 import QtCore, QtGui, QtWidgets


class MainWindow(QtWidgets.QMainWindow):

    _windowIcon = ':/icons/fugue/leaf-plant.png'
    _windowTitle = 'wic'
    _authenticationEnabled = True
    # whether to allow unconditional quit (if some forms didn't close)
    _unconditionalQuit = True

    def __init__(self, parent = None):
        super().__init__(parent)

        self.setWindowTitle(self._windowTitle)
        self.setWindowIcon(QtGui.QIcon(self._windowIcon))

        mdiArea = QtWidgets.QMdiArea()
        mdiArea.setDocumentMode(True)
        mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mdiArea.setViewMode(mdiArea.TabbedView)
        mdiArea.setTabPosition(QtWidgets.QTabWidget.North)
        mdiArea.setActivationOrder(mdiArea.ActivationHistoryOrder)
        mdiArea.subWindowActivated.connect(self.onSubwindowActivated)
        self.setCentralWidget(mdiArea)
        self.mdiArea = mdiArea

        tabBar = mdiArea.findChildren(QtWidgets.QTabBar)[0] # hack: http://www.qtforum.org/article/31711/close-button-on-tabs-of-mdi-windows-qmdiarea-qmdisubwindow-workaround.html
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


        from wic import settings
        self.settings = settings.Settings(self)

        self.setupMenu()

        if self._authenticationEnabled:
            self.authenticate()
        # when event loop is working
        QtCore.QTimer.singleShot(0, self.on_system_started)

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
        if self.on_system_about_to_quit() is False: # именно False, иначе None тоже считается отрицательным
            event.ignore()
            return
        self.settings.save()

    def restoreSubwindows(self):
        for window in self.mdiArea.subWindowList():
            window.showNormal()

    def minimizeSubwindows(self):
        for window in self.mdiArea.subWindowList():
            window.showMinimized()

    def addSubWindow(self, widget): # https://bugreports.qt.nokia.com/browse/QTBUG-9462
        """Add a new subwindow with the given widget
        """
        subWindow = QtWidgets.QMdiSubWindow() # no parent
        subWindow.setWidget(widget)
        subWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.mdiArea.addSubWindow(subWindow)
        subWindow.setWindowIcon(widget.windowIcon())
        subWindow.show()
        from wic import forms
        if isinstance(widget, forms.Form):
            widget.closed.connect(subWindow.close) # when form closes - close subWindow too
        return subWindow

    def authenticate(self):
        """Ask for credentials and check if the user is allowed to enter the system.
        """

    def requestQuit(self, unconditional = False):
        """Request application quit.
        """
        #self._unconditionalQuit = unconditional
        self.close() # TODO: check for self._unconditionalQuit when closing forms and mainWindow

    def on_system_started(self):
        """Called on startup when everything is ready.
        """

    def on_system_about_to_quit(self):
        """Called when the app is requested to quit. Return False to cancel
        """

    def show_warning(self, title, text):
        """Convenience function to show a warning message box.
        """
        QtWidgets.QMessageBox.warning(self, title, text)

    def show_information(self, title, text):
        """Convenience function to show an information message box.
        """
        QtWidgets.QMessageBox.information(self, title, text)


class TabBarEventFilter(QtCore.QObject):
    """Event filter for main window's tab bar.
    """
    def eventFilter(self, tabBar, event):
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() == QtCore.Qt.LeftButton:
                self.parent().onTabBarLeftDblClick()
                return True  # message processed
        return super().eventFilter(tabBar, event)  # standard event processing


def exception_hook(excType, excValue, excTraceback): 
    """Global function to catch unhandled exceptions (mostly in user modules).
    """
    info = ''.join(traceback.format_exception(excType, excValue, excTraceback))
    print(info)


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
