from PyQt4 import QtCore, QtGui

import wic


# PyQt4 installs an input hook (using PyOS_InputHook) that processes events when an interactive
# interpreter is waiting for user input. But it breaks ipdb, so we disable it.
QtCore.pyqtRemoveInputHook()


class WApp(QtGui.QApplication):

    _organizationName = 'vic'
    _applicationName = 'wic'

    def __init__(self, argv, MainWindowClass):
        if wic.app:
            raise Exception('There can be only one WApp instance')
        super().__init__(argv)

        self.setOrganizationName(self._organizationName)
        self.setApplicationName(self._applicationName)

        self.mainWindow = MainWindowClass()

        wic.app = self.mainWindow

        self.mainWindow.show() # show the main wndow
