import os, sys
from PyQt4 import QtCore, QtGui

from wic.w import printMessage
from wic.forms import WForm


class Form(WForm):
    ''''''

    def setupUi(self):
        super().setupUi()

        aboutInfo = '''<h3>Несколько слов об этой платформе.</h3>
        Данная платформа называется 'wic' - получше названия не придумал пока что :)
        
        Автор <a href="mailto:victor.varvariuc@gmail.com">Виктор Варварюк</a>.
        
        Это приложение использует замечательные <a href="http://p.yusukekamiyamane.com/">Fugue Icons</a>.'''
        self.labelAboutInfo.setText(aboutInfo.replace('\n', '<br>'))
        
        import platform
        systemInfo = '''Python %s, Qt %s, PyQt %s, OS %s''' % (platform.python_version(),
                    QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR, platform.system())
        self.labelSystemInfo.setText(systemInfo)