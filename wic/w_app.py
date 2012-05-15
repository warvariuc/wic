from PyQt4 import QtCore, QtGui

import wic


class WApp(QtGui.QApplication):

    _organizationName = 'vic'
    _applicationName = 'wic'

    def __init__(self, argv, MainWindowClass):
        if wic.app:
            raise Exception('There can be only one WApp instance')
        super().__init__(argv)

        wic.app = self

        self.setOrganizationName(self._organizationName)
        self.setApplicationName(self._applicationName)

        self.mainWindow = MainWindowClass()
        self.mainWindow.show() # show the main wndow
