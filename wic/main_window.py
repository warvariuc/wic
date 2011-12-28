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
        self.mdiArea.subWindowActivated.connect(self.onSubwindowActivated)

        self.mdiArea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiArea.setTabPosition(QtGui.QTabWidget.North)
        self.mdiArea.setActivationOrder(self.mdiArea.ActivationHistoryOrder)

        self.setCentralWidget(self.mdiArea)
        self.statusBar() # create status bar

        tabBar = self.mdiArea.findChildren(QtGui.QTabBar)[0] # hack: http://www.qtforum.org/article/31711/close-button-on-tabs-of-mdi-windows-qmdiarea-qmdisubwindow-workaround.html
        tabBar.setTabsClosable(True)
        tabBar.setExpanding(False)
        tabBar.setMovable(True)
        tabBar.setDrawBase(True)
        #tabBar.setShape(tabBar.TriangularSouth)
        tabBar.setSelectionBehaviorOnRemove(tabBar.SelectPreviousTab)
        tabBar.tabCloseRequested.connect(self.closeTab)
        self.tabBar = tabBar

        from wic.messages_window import MessagesWindow
        self.messagesWindow = MessagesWindow(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.messagesWindow)

        self.menu = menu.MainMenu(self)

        self.setWindowTitle('wic')

        from wic import w_settings
        self.settings = w_settings.WSettings(self)

    def closeTab(self, windowIndex):
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

    def windowRestoreAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showNormal()

    def windowMinimizeAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showMinimized()

    def onSubwindowActivated(self, subwindow): #http://doc.trolltech.com/latest/qmdiarea.html#subWindowActivated
        saveActive = bool(subwindow and subwindow.isWindowModified())
        #self.fileSaveAction.setEnabled(saveActive)
