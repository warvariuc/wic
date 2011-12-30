"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import os, sys

from PyQt4 import QtCore, QtGui

from wic import menu


class WMainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.mdiArea = QtGui.QMdiArea()
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiArea.setTabPosition(QtGui.QTabWidget.North)
        self.mdiArea.setActivationOrder(self.mdiArea.ActivationHistoryOrder)
        self.mdiArea.subWindowActivated.connect(self.onSubwindowActivated)
        self.setCentralWidget(self.mdiArea)

        tabBar = self.mdiArea.findChildren(QtGui.QTabBar)[0] # hack: http://www.qtforum.org/article/31711/close-button-on-tabs-of-mdi-windows-qmdiarea-qmdisubwindow-workaround.html
        tabBar.setTabsClosable(True)
        tabBar.setExpanding(False)
        tabBar.setMovable(True)
        tabBar.setDrawBase(True)
        #tabBar.setShape(tabBar.TriangularSouth)
        #tabBar.setIconSize(QtCore.QSize(16, 16))
        tabBar.setSelectionBehaviorOnRemove(tabBar.SelectPreviousTab)
        tabBar.tabCloseRequested.connect(self.onTabCloseRequested)
        self.tabBar = tabBar

        self.statusBar() # create status bar

        from wic.messages_window import MessagesWindow
        self.messagesWindow = MessagesWindow(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.messagesWindow)

        self.menu = menu.MainMenu(self)

        self.setWindowTitle('wic')

        from wic import w_settings
        self.settings = w_settings.WSettings(self)

    def onSubwindowActivated(self, subWindow): # http://doc.trolltech.com/latest/qmdiarea.html#subWindowActivated
        #self.mdiArea.setActiveSubWindow(subWindow)
        saveActive = bool(subWindow and subWindow.isWindowModified())
        #self.fileSaveAction.setEnabled(saveActive)

    def onTabCloseRequested(self, windowIndex):
        subWindow = self.mdiArea.subWindowList()[windowIndex]
        subWindow.close()

    def closeEvent(self, event):
        self.mdiArea.closeAllSubWindows() # Passes a close event from main window to all subwindows.
        if self.mdiArea.subWindowList(): # there are still open subwindows
            event.ignore()
            return
        from wic import app
        if app.onSystemAboutToExit() == False: # именно False, иначе None тоже считается отрицательным
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
