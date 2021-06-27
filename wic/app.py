from PyQt5 import QtCore, QtGui, QtWidgets

import wic


class App(QtWidgets.QApplication):

    _organizationName = 'vic'
    _applicationName = 'wic'

    def __init__(self, argv, MainWindowClass):
        if wic._app:
            raise Exception('There can be only one App instance')
        super().__init__(argv)

        self.setOrganizationName(self._organizationName)
        self.setApplicationName(self._applicationName)

        self.mainWindow = MainWindowClass()

        wic._app = self.mainWindow

        self.mainWindow.show()
