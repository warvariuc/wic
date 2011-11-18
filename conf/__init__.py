import sys, os
from PyQt4 import QtCore, QtGui

import wic
from wic import w
import orm
from wic.forms import openForm, openCatalogItemForm
from conf import settings

confDir = os.path.dirname(os.path.abspath(__file__))

def on_systemStarted(): # предопределенная процедура запускаемая при начале работы системы - when the core is ready
    w.statusBar.showMessage('Готов...', 5000)
    w.printMessage('<b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
    w.printMessage('Каталог приложения: ' + wic.appDir, False, False)
    w.printMessage('Каталог конфигурации: ' + w.confDir, False, False)

    global db
    db = orm.SqliteAdapter(settings.dbUri)

    from conf.reports.test import Form
    openForm(Form)
    
    from conf.catalogs.books import Books
    book = Books.getOne(db, where= (Books.price > 14))
    w.printMessage(db.getLastQuery())

    openCatalogItemForm(book)
    
    wic.mainWindow.windowRestoreAll()

    
def on_systemAboutToExit(): # предопределенная процедура запускаемая при завершении работы системы
    return True


def test():
    QtGui.QMessageBox.information(w.mainWindow, 'test', 'Это сообщение из процедуры глобального модуля')
