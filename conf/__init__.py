import sys, os
from PyQt4 import QtCore, QtGui
from wic import w
import wic


def on_SystemStart(): # предопределенная процедура запускаемая при начале работы системы
    w.statusBar.showMessage('Готов...', 5000)
    w.printMessage('<b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
    w.printMessage('Каталог приложения: ' + wic.appDir, False, False)
    w.printMessage('Каталог конфигурации: ' + w.confDir, False, False)

    from wic.forms import openForm, openCatalogItemForm
    from conf.catalogs.persons import Persons
    openForm('conf.reports.test')
    for person in Persons.get(wic.db, where= (Persons.last_name == 'Varvariuc'), limit= (0,5)):
        openCatalogItemForm(person)

    
def on_systemAboutToExit(): # предопределенная процедура запускаемая при завершении работы системы
    return True


def test():
    QtGui.QMessageBox.information(w.mainWindow, 'test', 'Это сообщение из процедуры глобального модуля')
