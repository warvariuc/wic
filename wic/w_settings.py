from PyQt4 import QtGui, QtCore

class WSettings():
    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

        self.path = QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DataLocation)
        #self.settings = QtCore.QSettings(QtCore.QSettings.IniFormat, QtCore.QSettings.UserScope, 'vic', 'wic')
        #path = 'd:\\wic_settings.ini'
        self.settings = QtCore.QSettings(self.path, QtCore.QSettings.IniFormat, self.mainWindow)


    def readSettings(self):
        #self.settings.beginGroup("/windows")
        geometry = self.settings.value('geometry', None)
        if geometry: self.mainWindow.restoreGeometry(geometry)
        windowState = self.settings.value('windowState', None)
        if windowState: self.mainWindow.restoreState(windowState)
        self.mainWindow.messagesWindow.setVisible(bool(int(self.settings.value('showMessagesWindow', True))))

        self.recentFiles = self.settings.value('recentFiles', None)
        if self.recentFiles is None: self.recentFiles = []
        
        self.lastUsedDirectory = self.settings.value('lastUsedDirectory', '')
        #self.settings.endGroup()

    def saveSettings(self):
        self.settings.setValue('geometry', self.mainWindow.saveGeometry())
        self.settings.setValue('windowState', self.mainWindow.saveState())
        self.settings.setValue('showMessagesWindow', int(self.mainWindow.messagesWindow.isVisible()))
        self.settings.setValue('recentFiles', self.recentFiles)
        self.settings.setValue('lastUsedDirectory', self.lastUsedDirectory)

