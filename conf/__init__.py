import sys, os
from PyQt4 import QtCore, QtGui

import wic
from wic import w
import orm
from wic.forms import openForm, openCatalogItemForm, openCatalogForm
from conf import settings

confDir = os.path.dirname(os.path.abspath(__file__))

def onSystemStarted(): # предопределенная процедура запускаемая при начале работы системы - when the core is ready
    w.statusBar.showMessage('Ready...', 5000)
    w.printMessage('<b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
    print('Каталог приложения: ' + wic.appDir)
    print('Каталог конфигурации: ' + confDir)

    global db
    db = orm.SqliteAdapter(settings.dbUri)

#    from conf.reports.test import Form
#    openForm(Form)
    
#    from conf.reports.repayment_schedule import Form
#    openForm(Form)
    
    from conf.catalogs.books import Books
    book = Books.getOne(db, where= (Books.price > 14))
#    w.printMessage(db.getLastQuery())
#
    openCatalogItemForm(book)
#    openCatalogItemForm(Books(db))
#    
#    wic.mainWindow.windowRestoreAll()

    from conf.catalogs.books import Books
    openCatalogForm(Books, db)

    
def onSystemAboutToExit(): # предопределенная процедура запускаемая при завершении работы системы
    return True


def test():
    QtGui.QMessageBox.information(w.mainWindow, 'test', 'Это сообщение из процедуры `глобального` модуля')
