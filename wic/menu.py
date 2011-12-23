"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import os

from PyQt4 import QtGui


class MainMenu():

    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

        self.file = mainWindow.menuBar().addMenu('File')
        self.open = createAction(mainWindow, 'Open…', mainWindow.onFileOpen, QtGui.QKeySequence.Open, ':/icons/fugue/folder-open-document-text.png')
        self.save = createAction(mainWindow, 'Save', mainWindow.onFileSave, QtGui.QKeySequence.Save, ':/icons/fugue/disk-black.png')
        self.quitApp = createAction(mainWindow, 'Quit', mainWindow.close, QtGui.QKeySequence.Quit, ':/icons/fugue/cross-button.png')

        addItemsToMenu(self.file, (self.open,))
        self.recentFiles = self.file.addMenu(QtGui.QIcon(':/icons/fugue/folders-stack.png'), 'Recent files')
        self.recentFiles.aboutToShow.connect(self.updateRecentFiles)
        addItemsToMenu(self.file, (self.save, self.quitApp))

        self.service = mainWindow.menuBar().addMenu('Service')
        addItemsToMenu(self.service, (
            createAction(mainWindow, 'Calculator', mainWindow.showCalculator, 'Ctrl+F2', ':/icons/fugue/calculator-scientific.png'),
            createAction(mainWindow, 'Calendar', mainWindow.showCalendar, icon = ':/icons/fugue/calendar-blue.png'),
            None,
            createAction(mainWindow, 'Database…', mainWindow.editDbInfo, None, ':/icons/fugue/database.png', 'Database connection'),
            createAction(mainWindow, 'Qt Designer', mainWindow.openQtDesigner, None, ':/icons/fugue/application-form.png', 'Run Designer with custom widgets'),
        ))

        self.windows = mainWindow.menuBar().addMenu('Windows')

        self.help = mainWindow.menuBar().addMenu('Help')
        addItemsToMenu(self.help, (
            createAction(mainWindow, 'About application', mainWindow.helpAbout, 'F1', ':/icons/fugue/question-button.png', 'See information about this application'),
        ))

        self.showMessagesWindow = createAction(mainWindow, 'Messages window', mainWindow.showMessagesWindow, 'F12', tip = 'Show/hide messages window', checkable = True)

        self.windowsStandard = (
            createAction(mainWindow, 'Next', mainWindow.mdiArea.activateNextSubWindow, QtGui.QKeySequence.NextChild),
            createAction(mainWindow, 'Previous', mainWindow.mdiArea.activatePreviousSubWindow, QtGui.QKeySequence.PreviousChild),
            createAction(mainWindow, 'Cascade', mainWindow.mdiArea.cascadeSubWindows),
            createAction(mainWindow, 'Tile', mainWindow.mdiArea.tileSubWindows),
            createAction(mainWindow, 'Restore All', mainWindow.windowRestoreAll),
            createAction(mainWindow, 'Iconize All', mainWindow.windowMinimizeAll),
            None, # separator
            createAction(mainWindow, 'Close', mainWindow.mdiArea.closeActiveSubWindow, QtGui.QKeySequence.Close, ':/icons/fugue/cross-white.png', 'Закрыть активное окно'),
            None,
            self.showMessagesWindow,
        )
        self.windows.aboutToShow.connect(self.updateWindowMenu) # Before window menu is shown, update the menu with the titles of each open window

    def updateWindowMenu(self):
        """Create windows menu with actions to jump to any open subwindow."""
        self.showMessagesWindow.setChecked(self.mainWindow.messagesWindow.isVisible()) # set checked here instead of catching visibilitychanged event
        menu = self.windows
        menu.clear()
        addItemsToMenu(menu, self.windowsStandard)
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



def createAction(widget, text, slot = None, shortcut = None, icon = None, tip = None, checkable = False, signal = 'triggered'):
    """Convenience function to create PyQt actions"""
    action = QtGui.QAction(text, widget)
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


def addItemsToMenu(menu, items):
    """Add multiple actions/menus to a menu"""
    for item in items:
        if isinstance(item, QtGui.QAction):
            menu.addAction(item)
        elif isinstance(item, QtGui.QMenu):
            menu.addMenu(item)
        else:
            menu.addSeparator()
