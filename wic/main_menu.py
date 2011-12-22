from PyQt4 import QtCore, QtGui
from wic import Bunch


def createMenu(mainWindow):
    menu = Bunch()

    menu.file = mainWindow.menuBar().addMenu('File')
    menu.open = createAction(mainWindow, 'Open…', mainWindow.onFileOpen, QtGui.QKeySequence.Open, ':/icons/fugue/folder-open-document-text.png')
    menu.save = createAction(mainWindow, 'Save', mainWindow.onFileSave, QtGui.QKeySequence.Save, ':/icons/fugue/disk-black.png')
    menu.quitApp = createAction(mainWindow, 'Quit', mainWindow.close, QtGui.QKeySequence.Quit, ':/icons/fugue/cross-button.png')

    addItemsToMenu(menu.file, (menu.open,))
    menu.recentFiles = menu.file.addMenu(QtGui.QIcon(':/icons/fugue/folders-stack.png'), 'Recent files')
    menu.recentFiles.aboutToShow.connect(mainWindow.updateRecentFiles)
    addItemsToMenu(menu.file, (menu.save, menu.quitApp))

    menu.service = mainWindow.menuBar().addMenu('Service')
    addItemsToMenu(menu.service, (
        createAction(mainWindow, 'Calculator', mainWindow.showCalculator, 'Ctrl+F2', ':/icons/fugue/calculator-scientific.png'),
        createAction(mainWindow, 'Calendar', mainWindow.showCalendar, icon=':/icons/fugue/calendar-blue.png'),
        None,
        createAction(mainWindow, 'Database…', mainWindow.editDbInfo, None, ':/icons/fugue/database.png', 'Database connection'),
        createAction(mainWindow, 'Qt Designer', mainWindow.openQtDesigner, None, ':/icons/fugue/application-form.png', 'Run Designer with custom widgets'),
    ))

    menu.windows = mainWindow.menuBar().addMenu('Windows')

    menu.help = mainWindow.menuBar().addMenu('Help')
    addItemsToMenu(menu.help, (
        createAction(mainWindow, 'About application', mainWindow.helpAbout, 'F1', ':/icons/fugue/question-button.png', 'See information about this application'),
    ))

    menu.messagesWindow = createAction(mainWindow, 'Messages window', mainWindow.showMessagesWindow, 'F12', tip='Show/hide messages window', checkable=True)

    menu.windowsStandard = (
        createAction(mainWindow, 'Next', mainWindow.mdiArea.activateNextSubWindow, QtGui.QKeySequence.NextChild),
        createAction(mainWindow, 'Previous', mainWindow.mdiArea.activatePreviousSubWindow, QtGui.QKeySequence.PreviousChild),
        createAction(mainWindow, 'Cascade', mainWindow.mdiArea.cascadeSubWindows),
        createAction(mainWindow, 'Tile', mainWindow.mdiArea.tileSubWindows),
        createAction(mainWindow, 'Restore All', mainWindow.windowRestoreAll),
        createAction(mainWindow, 'Iconize All', mainWindow.windowMinimizeAll),
        None, # separator
        createAction(mainWindow, 'Close', mainWindow.mdiArea.closeActiveSubWindow, QtGui.QKeySequence.Close, ':/icons/fugue/cross-white.png', 'Закрыть активное окно'),
        None,
        menu.messagesWindow,
    )
    menu.windows.aboutToShow.connect(mainWindow.updateWindowMenu) # Before window menu is shown, update the menu with the titles of each open window

    return menu


def createAction(widget, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal='triggered'):
    '''Convenience function to create PyQt actions'''
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
    '''Add multiple actions/menus to a menu'''
    for item in items:
        if isinstance(item, QtGui.QAction):
            menu.addAction(item)
        elif isinstance(item, QtGui.QMenu):
            menu.addMenu(item)
        else:
            menu.addSeparator()
