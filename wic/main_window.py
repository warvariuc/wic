"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

from PyQt4 import QtCore, QtGui


class TabBarEventFilter(QtCore.QObject):
    """Event filter for main window's tab bar."""

    def eventFilter(self, tabBar, event):
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() == QtCore.Qt.LeftButton:
                self.parent().onTabBarLeftDblClick()
                return True
        return super().eventFilter(tabBar, event) # standard event processing        


class WMainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

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

        from wic import menus
        self.menu = menus.MainMenu(self)

        self.setWindowTitle('wic')

        from wic import w_settings
        self.settings = w_settings.WSettings(self)

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
        from wic import app
        if app.onSystemAboutToQuit() is False: # именно False, иначе None тоже считается отрицательным
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
        """Add a new subwindow with the given widget"""
        subWindow = QtGui.QMdiSubWindow() # no parent
        subWindow.setWidget(widget)
        subWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.mdiArea.addSubWindow(subWindow)
        subWindow.setWindowIcon(widget.windowIcon())
        subWindow.show()
        widget.closed.connect(subWindow.close) # when form closes - close subWindow too
