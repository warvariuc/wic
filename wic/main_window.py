import os, sys
from PyQt4 import QtCore, QtGui

from wic import main_menu


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

        self.setCentralWidget(self.mdiArea)
        self.statusBar() # create status bar

        tabBar = self.mdiArea.findChildren(QtGui.QTabBar)[0] # hack: http://www.qtforum.org/article/31711/close-button-on-tabs-of-mdi-windows-qmdiarea-qmdisubwindow-workaround.html
        tabBar.setTabsClosable(True)
        tabBar.setExpanding(False)
        tabBar.setMovable(True)
        tabBar.setDrawBase(True)
        #tabBar.setShape(tabBar.TriangularSouth)
        tabBar.tabCloseRequested.connect(self.closeTab)
        self.tabBar = tabBar

        from wic.messages_window import MessagesWindow
        self.messagesWindow = MessagesWindow(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.messagesWindow)

        self.menus = main_menu.createMenus(self)

        self.setWindowTitle('wic')

        from wic import w_settings
        self.settings = w_settings.WSettings(self)
        self.settings.readSettings()


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

    def closeTab(self, windowIndex):
        subWindow = self.mdiArea.subWindowList()[windowIndex]
        subWindow.close()
        #self.mdiArea.removeSubWindow(subWindow)

    def closeEvent(self, event):
        self.mdiArea.closeAllSubWindows() # Passes a close event from main window to all subwindows.
        if self.mdiArea.subWindowList(): # there are still open subwindows
            event.ignore()
            return
        from wic import w
        if w.requestExit() == False: # именно False, иначе None тоже считается отрицательным
            event.ignore()
            return
        self.settings.saveSettings()

    def updateRecentFiles(self, filePath=''):
        '''Add a file to recent files list if file path given, otherwise update the menu.'''
        recentFiles = list(filter(os.path.isfile, self.settings.recentFiles)) # remove from the list non existing files

        if filePath:
            filePath = os.path.abspath(filePath)
            try: recentFiles.remove(filePath)
            except ValueError: pass
            recentFiles.insert(0, filePath)
            del recentFiles[10:] # keep only 10 of recently used files
        else:
            menu = self.menus.recentFiles
            menu.clear()
            for file in recentFiles:
                menu.addAction(QtGui.QIcon(':/icons/fugue/blue-folder-open-document-text.png'),
                               file, lambda file=file: self._openFile(file))
            if menu.isEmpty():
                noItemsAction = menu.addAction('Пусто')
                noItemsAction.setEnabled(False)

    def onFileOpen(self):
        filePath = QtGui.QFileDialog.getOpenFileName(self,
                'Открыть файл', self.settings.lastUsedDirectory, 'Модули (*.py);;Формы (*.ui);;Все файлы (*.*)')
        if filePath:
            self.settings.lastUsedDirectory = os.path.dirname(filePath)
            self._openFile(filePath)
            self.updateRecentFiles(filePath) # add to recent files if the opening was successful

    def _openFile(self, filePath):
        if filePath.endswith('.ui'):
            self.openQtDesigner(filePath)
        else:
            __import__('w').loadModule(filePath)

    def openQtDesigner(self, filePath=None):
        import subprocess, wic
        os.putenv('PYQTDESIGNERPATH', os.path.join(wic.appDir, 'widgets'))
        os.putenv('PATH', os.getenv('PATH', '') + ';' + os.path.dirname(sys.executable)) #designer needs python.dll to use python based widgets. on windows the dll is not in system32
        params = ['designer']
        if filePath:
            params.append(filePath)
        subprocess.Popen(params)


    def onFileSave(self):
        QtGui.QMessageBox.warning(self, 'Not implemented', 'This feature is not yet implemented')

    def showMessagesWindow(self):
        self.messagesWindow.setVisible(self.menus.actions.messagesWindow.isChecked())

    def windowRestoreAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showNormal()

    def windowMinimizeAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showMinimized()

    def updateWindowMenu(self):
        self.menus.actions.messagesWindow.setChecked(self.messagesWindow.isVisible()) #set checked here instead of catching visibilitychanged event
        #Creates a window menu with actions to jump to any open subwindow.
        menu = self.menus.windows
        menu.clear()
        main_menu.addItemsToMenu(self.menus.windows, self.menus.actions.windowsStandard)
        windows = self.mdiArea.subWindowList()
        if windows:
            menu.addSeparator()
            for i, window in enumerate(windows):
                title = window.windowTitle()
                if i == 10:
                    self.windowMenu.addSeparator()
                    menu = menu.addMenu('&More')
                accel = ''
                if i < 10:
                    accel = '&%i ' % i
                elif i < 36:
                    accel = '&%c ' % chr(i + ord('@') - 9)
                menu.addAction('%s%s' % (accel, title), lambda w=window: self.mdiArea.setActiveSubWindow(w))

    def onSubwindowActivated(self, subwindow): #http://doc.trolltech.com/latest/qmdiarea.html#subWindowActivated
        save_active = False
        if subwindow and subwindow.isWindowModified():
            save_active = True
        #self.fileSaveAction.setEnabled(save_active)
