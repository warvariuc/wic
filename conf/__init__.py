import sys, os
from PyQt4 import QtCore, QtGui

import wic
from wic import w
import orm
from wic.forms import openForm, openCatalogItemForm


def on_systemStart(): # предопределенная процедура запускаемая при начале работы системы - when the core is ready
    w.statusBar.showMessage('Готов...', 5000)
    w.printMessage('<b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
    w.printMessage('Каталог приложения: ' + wic.appDir, False, False)
    w.printMessage('Каталог конфигурации: ' + w.confDir, False, False)

    global db
    db = orm.SqliteAdapter('sqlite://../../mtc.sqlite')

    from conf.catalogs.persons import Persons
    openForm('conf.reports.test')
    for person in Persons.get(db, where= (orm.UPPER(Persons.last_name) == 'VARVARIUC'), limit= (0,5)):
        openCatalogItemForm(person)
    
    w.printMessage(db.getLastQuery())

    
def on_systemAboutToExit(): # предопределенная процедура запускаемая при завершении работы системы
    return True


def test():
    QtGui.QMessageBox.information(w.mainWindow, 'test', 'Это сообщение из процедуры глобального модуля')
