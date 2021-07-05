import os

from PyQt5 import QtGui, QtWidgets


class MainMenu():

    def __init__(self, main_window):
        self.main_window = main_window

        self.file = self.add_menu('File')
        self.open = create_action(
            main_window, 'Open…', self.on_file_open, QtGui.QKeySequence.Open,
            icon=':/icons/fugue/folder-open-document-text.png')
        self.save = create_action(
            main_window, 'Save', self.onFileSave, QtGui.QKeySequence.Save,
            icon=':/icons/fugue/disk-black.png')
        self.quitApp = create_action(
            main_window, 'Quit', main_window.close, QtGui.QKeySequence.Quit,
            icon=':/icons/fugue/cross-button.png')

        add_actions_to_menu(self.file, self.open)
        self.recent_files = self.file.addMenu(
            QtGui.QIcon(':/icons/fugue/folders-stack.png'), 'Recent files')
        self.recent_files.aboutToShow.connect(self.make_recent_files)
        add_actions_to_menu(self.file, self.save, self.quitApp)

        self.service = self.add_menu('Service')
        add_actions_to_menu(self.service,
            create_action(main_window, 'Calculator', self.show_calculator, 'Ctrl+F2',
                          icon=':/icons/fugue/calculator-scientific.png'),
            create_action(main_window, 'Calendar', self.show_calendar, None,
                          icon=':/icons/fugue/calendar-blue.png'),
            None,
            create_action(main_window, 'Database…', self.edit_db_info, None,
                          icon=':/icons/fugue/database.png', tip='Database connection'),
            create_action(main_window, 'Qt Designer', self.openQtDesigner, None,
                          icon=':/icons/fugue/application-form.png',
                          tip='Run Designer with custom widgets'),
        )

        self.catalogs = self.add_menu('Catalogs')
        self.reports = self.add_menu('Reports')
        self.windows = self.add_menu('Windows')

        self.help = self.add_menu('Help')
        add_actions_to_menu(self.help,
            create_action(main_window, 'About application', self.help_about, 'F1',
                          icon=':/icons/fugue/question-button.png',
                          tip='See information about this application'))

        self.show_messages_window_action = create_action(
            main_window, 'Messages window', self.show_messages_window, 'F12',
            tip='Show/hide messages window', checkable=True)

        self.windows_standard_menu = (
            create_action(main_window, 'Next', main_window.mdi_area.activateNextSubWindow,
                          QtGui.QKeySequence.NextChild),
            create_action(main_window, 'Previous', main_window.mdi_area.activatePreviousSubWindow,
                          QtGui.QKeySequence.PreviousChild),
            create_action(main_window, 'Cascade', main_window.mdi_area.cascadeSubWindows),
            create_action(main_window, 'Tile', main_window.mdi_area.tileSubWindows),
            create_action(main_window, 'Restore All', main_window.restore_subwindows),
            create_action(main_window, 'Iconize All', main_window.minimize_subwindows),
            None,  # separator
            create_action(main_window, 'Close', main_window.mdi_area.closeActiveSubWindow,
                          QtGui.QKeySequence.Close,
                          icon=':/icons/fugue/cross-white.png', tip='Close the active window.'),
            None,  # separator
            self.show_messages_window_action,
        )
        # Before window menu is shown, update the menu with the titles of each open window
        self.windows.aboutToShow.connect(self.update_window_menu)

    def add_menu(self, *args):
        return self.main_window.menuBar().addMenu(*args)

    def update_window_menu(self):
        """Create windows menu with actions to jump to any open subwindow.
        """
        # set checked here instead of catching visibilitychanged event
        self.show_messages_window_action.setChecked(self.main_window.messagesWindow.isVisible())
        menu = self.windows
        menu.clear()
        add_actions_to_menu(menu, self.windows_standard_menu)
        windows = self.main_window.mdi_area.subWindowList()
        if not windows:
            return
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
            menu.addAction(f'{accel}{title}', lambda w = window: self.main_window.mdi_area.setActiveSubWindow(w))

    def add_to_recent_files(self, file_path):
        """Add a file to recent files list.
        """
        # remove from the list non existing files
        recent_files = list(filter(os.path.isfile, self.main_window.settings.recent_files))

        file_path = os.path.abspath(file_path)
        try:
            recent_files.remove(file_path)
        except ValueError:
            pass
        recent_files.insert(0, file_path)
        # keep only 10 of recently used files
        del recent_files[10:]

        self.main_window.settings.recent_files = recent_files

    def make_recent_files(self, file_path=''):
        recent_files = list(filter(os.path.isfile, self.main_window.settings.recent_files))
        menu = self.recent_files
        menu.clear()
        for file in recent_files:
            menu.addAction(QtGui.QIcon(':/icons/fugue/blue-folder-open-document-text.png'),
                           file, lambda f = file: self._open_file(f))
        if menu.isEmpty():
            no_items_action = menu.addAction('Пусто')
            no_items_action.setEnabled(False)

    def edit_db_info(self):
        from wic.forms import open_form, db_info
        open_form(db_info.Form)

    def help_about(self):
        from wic.forms import open_form, help_about
        open_form(help_about.Form, modal=True)

    def show_calculator(self):
        from wic.widgets import PopupCalculator
        PopupCalculator(self.main_window, persistent = True).show()

    def show_calendar(self):
        from wic.widgets import date_edit
        date_edit.CalendarPopup(self.main_window, persistent = True).show()

    def on_file_open(self):
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window, 'Open file', self.main_window.settings.last_used_dir,
            'Modules *.py(*.py);;Forms *.ui(*.ui);;All files *.*(*.*)')
        if not file_path:
            return
        self.main_window.settings.last_used_dir = os.path.dirname(file_path)
        self._open_file(file_path)
        # add to recent files if the opening was successful
        self.add_to_recent_files(file_path)

    def _open_file(self, file_path):
        if file_path.endswith('.ui'):
            self.openQtDesigner(file_path)
        else:
            print(file_path)

    def openQtDesigner(self, file_path =''):
        import sys, subprocess, wic

        os.putenv('PYQTDESIGNERPATH', os.path.join(wic.wic_dir, 'widgets'))
        os.putenv('PATH', os.getenv('PATH', '') + ';' + os.path.dirname(sys.executable)) # designer needs python.dll to use PyQt widgets. on windows the dll is not in system32
        params = ['designer']
        if file_path:
            params.append(file_path)
        subprocess.Popen(params)


    def onFileSave(self):
        self.main_window.show_warning('Not implemented', 'This feature is not yet implemented')

    def show_messages_window(self):
        self.main_window.messagesWindow.setVisible(self.show_messages_window_action.isChecked())



def create_action(
        parent, text, slot=None, shortcut= None, icon=None, tip=None, checkable=False,
        signal='triggered'):
    """Helper to create a QAction.
    """
    action = QtWidgets.QAction(text, parent)
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


def add_actions_to_menu(menu, *items):
    """Add multiple actions/menus to a menu.
    """
    assert hasattr(items, '__iter__'), 'Items argument must an iterable'
    for item in items:
        if isinstance(item, QtWidgets.QAction):
            menu.addAction(item)
        elif isinstance(item, QtWidgets.QMenu):
            menu.addMenu(item)
        else:
            menu.addSeparator()
