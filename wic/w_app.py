from PyQt4 import QtGui, QtCore
import os

class WApp(QtGui.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setWindowIcon(QtGui.QIcon(':/icons/fugue/leaf-plant.png'))
        self.setOrganizationName('vic')
        self.setApplicationName('wic')

