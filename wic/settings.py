from PyQt5 import QtGui, QtCore, QtWidgets


class Settings():
    def __init__(self, main_window):
        self.main_window = main_window

        self.path = QtCore.QStandardPaths.standardLocations(QtCore.QStandardPaths.DataLocation)[0]
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, 'vic', 'wic')
        #path = 'd:\\wic_settings.ini'
        self.settings = QtCore.QSettings(self.path, QtCore.QSettings.IniFormat, self.main_window)
        self.load()

    def load(self):
        #self.settings.beginGroup("/windows")
        geometry = self.settings.value('geometry', None)
        if geometry:
            self.main_window.restoreGeometry(geometry)
        window_state = self.settings.value('windowState', None)
        if window_state:
            self.main_window.restoreState(window_state)
        self.main_window.messagesWindow.setVisible(
            bool(int(self.settings.value('showMessagesWindow', True))))

        self.recent_files = self.settings.value('recentFiles', None)
        if self.recent_files is None:
            self.recent_files = []

        self.last_used_dir = self.settings.value('lastUsedDirectory', '')
        #self.settings.endGroup()

    def save(self):
        self.settings.setValue('geometry', self.main_window.saveGeometry())
        self.settings.setValue('windowState', self.main_window.saveState())
        self.settings.setValue('showMessagesWindow', int(self.main_window.messagesWindow.isVisible()))
        self.settings.setValue('recentFiles', self.recent_files)
        self.settings.setValue('lastUsedDirectory', self.last_used_dir)

