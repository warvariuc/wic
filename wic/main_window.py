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

    def editDbInfo(self):
        from wic.forms import openForm, db_info
        openForm(db_info.Form)

    def helpAbout(self):
        from wic.forms import openForm, help_about
        openForm(help_about.Form)

    def showCalculator(self):
        from wic.widgets import w_decimal_edit
        w_decimal_edit.WPopupCalculator(self, persistent=True).show()

    def showCalendar(self):
        from wic.widgets import w_date_edit
        w_date_edit.WCalendarPopup(self, persistent=True).show()

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

    def onFileOpen(self):
        filePath = QtGui.QFileDialog.getOpenFileName(self,
                'Открыть файл', self.settings.lastUsedDirectory, 'Модули (*.py);;Формы (*.ui);;Все файлы (*.*)')
        if filePath:
            self.settings.lastUsedDirectory = os.path.dirname(filePath)
            self._openFile(filePath)
            self.menu.updateRecentFiles(filePath) # add to recent files if the opening was successful

    def _openFile(self, filePath):
        if filePath.endswith('.ui'):
            self.openQtDesigner(filePath)
        else:
            __import__('w').loadModule(filePath)

    def openQtDesigner(self, filePath=None):
        import subprocess, wic
        os.putenv('PYQTDESIGNERPATH', os.path.join(wic.wicDir, 'widgets'))
        os.putenv('PATH', os.getenv('PATH', '') + ';' + os.path.dirname(sys.executable)) #designer needs python.dll to use python based widgets. on windows the dll is not in system32
        params = ['designer']
        if filePath:
            params.append(filePath)
        subprocess.Popen(params)


    def onFileSave(self):
        QtGui.QMessageBox.warning(self, 'Not implemented', 'This feature is not yet implemented')

    def showMessagesWindow(self):
        self.messagesWindow.setVisible(self.menu.showMessagesWindow.isChecked())

    def windowRestoreAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showNormal()

    def windowMinimizeAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showMinimized()

    def onSubwindowActivated(self, subwindow): #http://doc.trolltech.com/latest/qmdiarea.html#subWindowActivated
        saveActive = bool(subwindow and subwindow.isWindowModified())
        #self.fileSaveAction.setEnabled(saveActive)
