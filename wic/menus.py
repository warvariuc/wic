"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

import os

from PyQt4 import QtGui


class MainMenu():

    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

        self.file = self.addMenu('File')
        self.open = createAction(mainWindow, 'Open…', self.onFileOpen, QtGui.QKeySequence.Open, ':/icons/fugue/folder-open-document-text.png')
        self.save = createAction(mainWindow, 'Save', self.onFileSave, QtGui.QKeySequence.Save, ':/icons/fugue/disk-black.png')
        self.quitApp = createAction(mainWindow, 'Quit', mainWindow.close, QtGui.QKeySequence.Quit, ':/icons/fugue/cross-button.png')

        addActionsToMenu(self.file, (self.open,))
        self.recentFiles = self.file.addMenu(QtGui.QIcon(':/icons/fugue/folders-stack.png'), 'Recent files')
        self.recentFiles.aboutToShow.connect(self.updateRecentFiles)
        addActionsToMenu(self.file, (self.save, self.quitApp))

        self.service = self.addMenu('Service')
        addActionsToMenu(self.service, (
            createAction(mainWindow, 'Calculator', self.showCalculator, 'Ctrl+F2', ':/icons/fugue/calculator-scientific.png'),
            createAction(mainWindow, 'Calendar', self.showCalendar, icon = ':/icons/fugue/calendar-blue.png'),
            None,
            createAction(mainWindow, 'Database…', self.editDbInfo, None, ':/icons/fugue/database.png', 'Database connection'),
            createAction(mainWindow, 'Qt Designer', self.openQtDesigner, None, ':/icons/fugue/application-form.png', 'Run Designer with custom widgets'),
        ))

        self.catalogs = self.addMenu('Catalogs')
        self.reports = self.addMenu('Reports')
        self.windows = self.addMenu('Windows')

        self.help = self.addMenu('Help')
        addActionsToMenu(self.help, (
            createAction(mainWindow, 'About application', self.helpAbout, 'F1', ':/icons/fugue/question-button.png', 'See information about this application'),
        ))

        self.showMessagesWindow = createAction(mainWindow, 'Messages window', self.showMessagesWindow, 'F12', tip = 'Show/hide messages window', checkable = True)

        self.windowsStandard = (
            createAction(mainWindow, 'Next', mainWindow.mdiArea.activateNextSubWindow, QtGui.QKeySequence.NextChild),
            createAction(mainWindow, 'Previous', mainWindow.mdiArea.activatePreviousSubWindow, QtGui.QKeySequence.PreviousChild),
            createAction(mainWindow, 'Cascade', mainWindow.mdiArea.cascadeSubWindows),
            createAction(mainWindow, 'Tile', mainWindow.mdiArea.tileSubWindows),
            createAction(mainWindow, 'Restore All', mainWindow.restoreSubwindows),
            createAction(mainWindow, 'Iconize All', mainWindow.minimizeSubwindows),
            None, # separator
            createAction(mainWindow, 'Close', mainWindow.mdiArea.closeActiveSubWindow, QtGui.QKeySequence.Close, ':/icons/fugue/cross-white.png', 'Закрыть активное окно'),
            None, # separator
            self.showMessagesWindow,
        )
        self.windows.aboutToShow.connect(self.updateWindowMenu) # Before window menu is shown, update the menu with the titles of each open window

    def addMenu(self, *args):
        return self.mainWindow.menuBar().addMenu(*args)

    def updateWindowMenu(self):
        """Create windows menu with actions to jump to any open subwindow."""
        self.showMessagesWindow.setChecked(self.mainWindow.messagesWindow.isVisible()) # set checked here instead of catching visibilitychanged event
        menu = self.windows
        menu.clear()
        addActionsToMenu(menu, self.windowsStandard)
        windows = self.mainWindow.mdiArea.subWindowList()
        if windows:
            menu.addSeparator()
            for i, window in enumerate(windows):
                title = window.windowTitle()
                if i == 10:
                    menu.addSeparator()
                    menu = menu.addMenu('&More')
                accel = ''
                if i < 10:
                    accel = '&%i ' % i
                elif i < 36:
                    accel = '&%c ' % chr(i + ord('@') - 9)
                menu.addAction('%s%s' % (accel, title), lambda w = window: self.mainWindow.mdiArea.setActiveSubWindow(w))

    def updateRecentFiles(self, filePath = ''):
        """Add a file to recent files list if file path given, otherwise update the menu."""
        recentFiles = list(filter(os.path.isfile, self.mainWindow.settings.recentFiles)) # remove from the list non existing files

        if filePath:
            filePath = os.path.abspath(filePath)
            try: recentFiles.remove(filePath)
            except ValueError: pass
            recentFiles.insert(0, filePath)
            del recentFiles[10:] # keep only 10 of recently used files
        else:
            menu = self.recentFiles
            menu.clear()
            for file in recentFiles:
                menu.addAction(QtGui.QIcon(':/icons/fugue/blue-folder-open-document-text.png'),
                               file, lambda f = file: self._openFile(f))
            if menu.isEmpty():
                noItemsAction = menu.addAction('Пусто')
                noItemsAction.setEnabled(False)



    def editDbInfo(self):
        from wic.forms import openForm, db_info
        openForm(db_info.Form)

    def helpAbout(self):
        from wic.forms import openForm, help_about
        openForm(help_about.Form, modal = True)

    def showCalculator(self):
        from wic.widgets import WPopupCalculator
        WPopupCalculator(self.mainWindow, persistent = True).show()

    def showCalendar(self):
        from wic.widgets import w_date_edit
        w_date_edit.WCalendarPopup(self.mainWindow, persistent = True).show()

    def onFileOpen(self):
        filePath = QtGui.QFileDialog.getOpenFileName(self.mainWindow,
                'Open file', self.settings.lastUsedDirectory, 'Modules (*.py);;Forms (*.ui);;All files (*.*)')
        if filePath:
            self.mainWindow.settings.lastUsedDirectory = os.path.dirname(filePath)
            self._openFile(filePath)
            self.updateRecentFiles(filePath) # add to recent files if the opening was successful

    def _openFile(self, filePath):
        if filePath.endswith('.ui'):
            self.openQtDesigner(filePath)
        else:
            print(filePath)

    def openQtDesigner(self, filePath = ''):
        import sys, subprocess, wic
        os.putenv('PYQTDESIGNERPATH', os.path.join(wic.wicDir, 'widgets'))
        os.putenv('PATH', os.getenv('PATH', '') + ';' + os.path.dirname(sys.executable)) # designer needs python.dll to use PyQt widgets. on windows the dll is not in system32
        params = ['designer']
        if filePath:
            params.append(filePath)
        subprocess.Popen(params)


    def onFileSave(self):
        QtGui.QMessageBox.warning(self, 'Not implemented', 'This feature is not yet implemented')

    def showMessagesWindow(self):
        self.mainWindow.messagesWindow.setVisible(self.showMessagesWindow.isChecked())



def createAction(parent, text, slot = None, shortcut = None, icon = None, tip = None, checkable = False, signal = 'triggered'):
    """Convenience function to create QActions"""
    action = QtGui.QAction(text, parent)
    if icon:
        action.setIcon(QtGui.QIcon(icon))
    if shortcut:
        action.setShortcut(shortcut)
    if tip:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if slot:
        getattr(action, signal).connect(slot)
    action.setCheckable(checkable)
    return action


def addActionsToMenu(menu, items):
    """Add multiple actions/menus to a menu"""
    assert hasattr(items, '__iter__'), 'Items argument must an iterable'
    for item in items:
        if isinstance(item, QtGui.QAction):
            menu.addAction(item)
        elif isinstance(item, QtGui.QMenu):
            menu.addMenu(item)
        else:
            menu.addSeparator()
