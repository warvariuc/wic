import sys, os
from PyQt4 import QtCore, QtGui
from wic import w


def system_started(): # предопределенная процедура запускаемая при начале работы системы
    w.statusBar.showMessage('Готов...', 5000)
    w.printMessage('<b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
    w.printMessage('Каталог приложения: ' + w.appDir, False, False)
    w.printMessage('Каталог конфигурации: ' + w.confDir, False, False)
    #w.loadModule(os.path.join(w.appDir, 'conf/reports/РасчетГрафикаПлатежей/module.py'))
    #w.loadModule(os.path.join(w.appDir, 'conf/reports/РасчетГрафикаПлатежей/module.py'))
    return True
    
def system_aboutToExit(): # предопределенная процедура запускаемая при завершении работы системы
    return True


def test():
    QtGui.QMessageBox.information(w.mainWindow, 'test', 'Это сообщение из процедуры глобального модуля')
