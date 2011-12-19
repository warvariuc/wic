from PyQt4 import QtCore, QtGui
from wic import Bunch


def createMenus(mainWindow):
    menus = Bunch()
    actions = Bunch()

    menus.file = mainWindow.menuBar().addMenu('File')
    actions.open = createAction(mainWindow, 'Open…', mainWindow.onFileOpen, QtGui.QKeySequence.Open, ':/icons/fugue/folder-open-document-text.png')
    actions.save = createAction(mainWindow, 'Save', mainWindow.onFileSave, QtGui.QKeySequence.Save, ':/icons/fugue/disk-black.png')
    actions.quitApp = createAction(mainWindow, 'Quit', mainWindow.close, QtGui.QKeySequence.Quit, ':/icons/fugue/cross-button.png')

    addItemsToMenu(menus.file, (actions.open,))
    menus.recentFiles = menus.file.addMenu(QtGui.QIcon(':/icons/fugue/folders-stack.png'), 'Recent files')
    menus.recentFiles.aboutToShow.connect(mainWindow.updateRecentFiles)
    addItemsToMenu(menus.file, (actions.save, actions.quitApp))

    menus.service = mainWindow.menuBar().addMenu('Service')
    addItemsToMenu(menus.service, (
        createAction(mainWindow, 'Calculator', mainWindow.showCalculator, 'Ctrl+F2', ':/icons/fugue/calculator-scientific.png'),
        createAction(mainWindow, 'Calendar', mainWindow.showCalendar, icon=':/icons/fugue/calendar-blue.png'),
        None,
        createAction(mainWindow, 'Database…', mainWindow.editDbInfo, None, ':/icons/fugue/database.png', 'Database connection'),
        createAction(mainWindow, 'Qt Designer', mainWindow.openQtDesigner, None, ':/icons/fugue/application-form.png', 'Run Designer with custom widgets'),
    ))

    menus.windows = mainWindow.menuBar().addMenu('Windows')

    menus.help = mainWindow.menuBar().addMenu('Help')
    addItemsToMenu(menus.help, (
        createAction(mainWindow, 'About application', mainWindow.helpAbout, 'F1', ':/icons/fugue/question-button.png', 'See information about this application'),
    ))

    actions.messagesWindow = createAction(mainWindow, 'Messages window', mainWindow.showMessagesWindow, 'F12', tip='Show/hide messages window', checkable=True)

    actions.windowsStandard = (
        createAction(mainWindow, 'Next', mainWindow.mdiArea.activateNextSubWindow, QtGui.QKeySequence.NextChild),
        createAction(mainWindow, 'Previous', mainWindow.mdiArea.activatePreviousSubWindow, QtGui.QKeySequence.PreviousChild),
        createAction(mainWindow, 'Cascade', mainWindow.mdiArea.cascadeSubWindows),
        createAction(mainWindow, 'Tile', mainWindow.mdiArea.tileSubWindows),
        createAction(mainWindow, 'Restore All', mainWindow.windowRestoreAll),
        createAction(mainWindow, 'Iconize All', mainWindow.windowMinimizeAll),
        None, # separator
        createAction(mainWindow, 'Close', mainWindow.mdiArea.closeActiveSubWindow, QtGui.QKeySequence.Close, ':/icons/fugue/cross-white.png', 'Закрыть активное окно'),
        None,
        actions.messagesWindow,
    )
    menus.windows.aboutToShow.connect(mainWindow.updateWindowMenu) # Before window menu is shown, update the menu with the titles of each open window

    menus.actions = actions
    return menus


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
