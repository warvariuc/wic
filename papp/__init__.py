"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import sys, os

from PyQt4 import QtCore, QtGui

import wic
import orm
from wic.forms import openForm, openCatalogItemForm, openCatalogForm
from wic.w_app import WApp
from . import settings

appDir = os.path.dirname(os.path.abspath(__file__))


class App(wic.w_app.WApp):

    def onSystemStarted(self): # предопределенная процедура запускаемая при начале работы системы - when the core is ready
        self.statusBar.showMessage('Ready...', 5000)
        self.printMessage('<b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
        print('Каталог приложения: ' + appDir)

        global db
        db = orm.SqliteAdapter(settings.dbUri)

    #    from conf.reports.test import Form
    #    openForm(Form)
    #    
    #    from conf.reports.repayment_schedule import Form
    #    openForm(Form)
    #    
        from .catalogs.books import Books
    #    book = Books.getOne(db, where= (Books.price > 14))
    #    print(db.getLastQuery())
    #
    #    openCatalogItemForm(book)
    #    openCatalogItemForm(Books(db))
    #    
    #    wic.mainWindow.windowRestoreAll()

        openCatalogForm(Books, db)


    def onSystemAboutToExit(self): # предопределенная процедура запускаемая при завершении работы системы
        return True


def test():
    wic.app.showInformation('test', 'Это сообщение из процедуры "глобального" модуля')
