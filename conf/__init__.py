"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import sys, os
from PyQt4 import QtCore, QtGui

import wic
import orm
from wic.forms import openForm, openCatalogItemForm, openCatalogForm
from conf import settings

confDir = os.path.dirname(os.path.abspath(__file__))

def onSystemStarted(): # предопределенная процедура запускаемая при начале работы системы - when the core is ready
    wic.statusBar.showMessage('Ready...', 5000)
    wic.printMessage('<b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
    print('Application directory: ' + wic.appDir)
    print('Каталог конфигурации: ' + confDir)

    global db
    db = orm.SqliteAdapter(settings.dbUri)

#    from conf.reports.test import Form
#    openForm(Form)
#    
#    from conf.reports.repayment_schedule import Form
#    openForm(Form)
#    
    from conf.catalogs.books import Books
#    book = Books.getOne(db, where= (Books.price > 14))
#    print(db.getLastQuery())
#
#    openCatalogItemForm(book)
#    openCatalogItemForm(Books(db))
#    
#    wic.mainWindow.windowRestoreAll()

    openCatalogForm(Books, db)

    
def onSystemAboutToExit(): # предопределенная процедура запускаемая при завершении работы системы
    return True


def test():
    wic.showInformation('test', 'Это сообщение из процедуры "глобального" модуля')
