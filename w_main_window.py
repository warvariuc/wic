from PyQt4 import QtCore, QtGui
import os, sys

class WMainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.mdiArea = QtGui.QMdiArea()
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.mdiArea.subWindowActivated.connect(self.handleSubwindowActivated)

        self.mdiArea.setViewMode(QtGui.QMdiArea.TabbedView)
        self.mdiArea.setTabPosition(QtGui.QTabWidget.North)
        tabBar = self.mdiArea.findChildren(QtGui.QTabBar)[ 0 ] # a hack: http://www.qtforum.org/article/31711/close-button-on-tabs-of-mdi-windows-qmdiarea-qmdisubwindow-workaround.html
        tabBar.setTabsClosable(True)
        tabBar.setExpanding(False)
        #tabBar.setMovable(True)
        tabBar.setDrawBase(True)
        #tabBar.setShape(tabBar.TriangularSouth)
        tabBar.tabCloseRequested.connect(self.closeTab)

        self.setCentralWidget(self.mdiArea)
        self.statusBar()
        
        from messages_window import MessagesWindow
        self.messagesWindow = MessagesWindow(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.messagesWindow.dockWidget)

        #Create menu
        self.fileMenu = self.menuBar().addMenu('Файл')
        fileOpenAction = self.createAction('Открыть…', self.handleFileOpen, QtGui.QKeySequence.Open, ':/icons/fugue/folder-open-document-text.png')
        
        self.fileSaveAction = self.createAction('Сохранить', self.fileSave, QtGui.QKeySequence.Save, ':/icons/fugue/disk-black.png')
        fileQuitAction = self.createAction('Выход', self.close, 'Ctrl+Q', ':/icons/fugue/cross-button.png')

        self.addActions(self.fileMenu, (fileOpenAction, ))
        self.recentFilesMenu = self.fileMenu.addMenu(QtGui.QIcon(':/icons/fugue/folders-stack.png'),'Недавние файлы')
        self.recentFilesMenu.aboutToShow.connect(self.updateRecentFiles)
        self.addActions(self.fileMenu, (self.fileSaveAction, fileQuitAction))

        self.serviceMenu = self.menuBar().addMenu('Сервис')
        self.addActions(self.serviceMenu, 
                    (self.createAction('Калькулятор', self.showCalculator, 'Ctrl+F2', ':/icons/fugue/calculator-scientific.png'), 
                    self.createAction('Календарь', self.showCalendar, icon=':/icons/fugue/calendar-blue.png'), 
                    None, 
                    self.createAction('База данных...', self.editDbInfo, icon=':/icons/fugue/database.png'), 
                    self.createAction('Дизайнер конфигурации', self.showDesigner, 'Alt+F11', ':/icons/fugue/block.png')))
                    
                   
        self.windowMenu = self.menuBar().addMenu('Окна')
        
        self.helpMenu = self.menuBar().addMenu('Помощь')
        self.addActions(self.helpMenu, (self.createAction('О программе', self.helpAbout, icon=':/icons/fugue/question-button.png'), ))

        self.windowMessagesAction = self.createAction('Окно сообщений', self.showMessagesWindow)
        self.windowMessagesAction.setCheckable(True)

        self.standardWindowActions = (
                self.createAction('Следующее', self.mdiArea.activateNextSubWindow, QtGui.QKeySequence.NextChild),
                self.createAction('Предыдущее', self.mdiArea.activatePreviousSubWindow, QtGui.QKeySequence.PreviousChild),
                self.createAction('Cascade', self.mdiArea.cascadeSubWindows),
                self.createAction('Tile', self.mdiArea.tileSubWindows),
                self.createAction('Restore All', self.windowRestoreAll),
                self.createAction('Iconize All', self.windowMinimizeAll),
                None, #separator
                self.createAction("Закрыть", self.mdiArea.closeActiveSubWindow, QtGui.QKeySequence.Close, ':/icons/fugue/cross-white.png'),
                None,
                self.windowMessagesAction)
        
        self.windowMenu.aboutToShow.connect(self.updateWindowMenu) #Before window menu is shown, update the menu with the titles of each open window

        self.setWindowTitle('wic')
        
        
        import w_settings
        self.settings = w_settings.WSettings(self)
        self.settings.readSettings()

    def editDbInfo(self):
        __import__('db_info').DbInfo(QtGui.qApp.confDir).edit(self)

    def showDesigner(self):
        __import__('w').loadModule(os.path.join(QtGui.qApp.appDir, 'designer.py'))

    def showCalculator(self):
        import w_decimal_edit
        w_decimal_edit.WPopupCalculator(self, persistent=True).show()
        
    def showCalendar(self):
        import w_date_edit
        w_date_edit.WCalendarPopup(self, persistent=True).show()

    def closeTab(self, i):
        subWindow = self.mdiArea.subWindowList()[i]
        subWindow.close()
        #self.mdiArea.removeSubWindow(subWindow)

    def closeEvent(self, event):
        self.mdiArea.closeAllSubWindows() #Passes a close event from main window to all subwindows.
        if self.mdiArea.subWindowList(): #there are still open subwindows
            event.ignore()
            return
        import w
        if w.requestExit() == False: #именно False, иначе None тоже считается отрицательным
            event.ignore()
            return
        self.settings.saveSettings()

    def updateRecentFiles(self, filePath=''):
        recentFiles = self.settings.recentFiles
        for i in range(len(recentFiles)-1, -1, -1): # remove from the list deleted files
            if not os.path.isfile(recentFiles[i]): del recentFiles[i]
            
        if filePath: #the funtion adds a file to recent files list if file name given otherwise updates the menu
            filePath = os.path.abspath(filePath)
            try: recentFiles.pop(recentFiles.index(filePath))
            except ValueError: pass
            recentFiles.insert(0, filePath)
            del recentFiles[10:] #keep 10 last files
            return
        menu = self.recentFilesMenu
        menu.clear()
        for file in recentFiles:
            menu.addAction(QtGui.QIcon(':/icons/fugue/blue-folder-open-document-text.png'), file, lambda file=file: self._openFile(file))
        if menu.isEmpty():
            noItemsAction = menu.addAction('Пусто')
            noItemsAction.setEnabled(False)
    
    def handleFileOpen(self):
        filePath = QtGui.QFileDialog.getOpenFileName(self,
                'Открыть файл', self.settings.lastUsedDirectory, 'Модули (*.py);;Формы (*.ui);;Все файлы (*.*)')
        if filePath: 
            self.settings.lastUsedDirectory = os.path.dirname(filePath)
            self._openFile(filePath)
            self.updateRecentFiles(filePath) # add to recent files if the opening was successful

    def _openFile(self, filePath):
        if filePath.endswith('.ui'):
            os.putenv('PYQTDESIGNERPATH', os.path.join(QtGui.qApp.appDir, 'widgets'))
            os.putenv('PATH', os.getenv('PATH', '') + ';' + os.path.dirname(sys.executable)) #designer needs python.dll to use python based widgets. on windows the dll is not in system32
            params = ['designer', filePath] # "designer-qt4" on Linux
            __import__('subprocess').Popen(params)
            return
        else:
            __import__('w').loadModule(filePath)

    def fileSave(self):
        QtGui.QMessageBox.warning(self, 'Not implemented', 'This feature is not yet implemented')

    def showMessagesWindow(self):
        self.messagesWindow.dockWidget.setVisible(self.windowMessagesAction.isChecked())

    def helpAbout(self):
        __import__('w_help_about').showAboutInfo(self)
        
    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False, signal='triggered'):
        #Convenience function to create PyQt actions
        action = QtGui.QAction(text, self)
        if icon is not None: action.setIcon(QtGui.QIcon(icon))
        if shortcut is not None: action.setShortcut(shortcut)
        if tip is not None: 
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None: 
            getattr(action, signal).connect(slot)
        action.setCheckable(checkable)
        return action

    def addActions(self, target, actions):
        #Add multiple actions to a menu
        for action in actions:
            if not action: target.addSeparator()
            else: target.addAction(action)

    def windowRestoreAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showNormal()

    def windowMinimizeAll(self):
        for window in self.mdiArea.subWindowList():
            window.widget().showMinimized()

    def updateWindowMenu(self):
        self.windowMessagesAction.setChecked(self.messagesWindow.dockWidget.isVisible()) #set checked here instead of catching visibilitychanged event
        #Creates a window menu with actions to jump to any open subwindow.
        menu = self.windowMenu
        menu.clear()
        self.addActions(self.windowMenu, self.standardWindowActions)
        windows = self.mdiArea.subWindowList()
        if not windows: return
        menu.addSeparator()
        for i, window in enumerate(windows):
            title = window.windowTitle()
            if i == 10:
                self.windowMenu.addSeparator()
                menu = menu.addMenu('&More')
            accel = ''
            if i < 10:
                accel = '&%d ' % i
            elif i < 36:
                accel = '&%c ' % chr(i + ord('@') - 9)
            menu.addAction("{}{}".format(accel, title),
                    lambda w=window: self.mdiArea.setActiveSubWindow(w)) #cannot remove parameter w in lambda - looks like var window changes otherwise if we use it

    def handleSubwindowActivated(self, subwindow): #http://doc.trolltech.com/latest/qmdiarea.html#subWindowActivated
        save_active = False
        if subwindow and subwindow.isWindowModified():
            save_active = True
        #self.fileSaveAction.setEnabled(save_active)
