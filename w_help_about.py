from PyQt4 import QtGui, QtCore
import platform

def showAboutInfo(mainWindow):
    QtGui.QMessageBox.about(mainWindow, 'wic', 
        """<h2>Несколько слов об этой платформе.</h2>\
        Данная платформа называется 'wic' - получше названия не придумал пока что :)
        Это моя попытка создать замену 1С. Получится или нет - зависит от настойчивости и обстоятельств.
        Лицензия будет открытой, зарабатывать ожидается на разработке и поддержке конфигураций.
        
        Автор <a href="mailto:victor.varvariuc@gmail.com">Виктор Варварюк</a>.
        
        Это приложение использует <a href="http://p.yusukekamiyamane.com/">Fugue Icons</a>.
        
        Информация о среде исполнения:
        Python {}, Qt {}, PyQt {}, OS {}""".replace('\n', '<br>').format(platform.python_version(),
        QtCore.QT_VERSION_STR, QtCore.PYQT_VERSION_STR, platform.system()))
