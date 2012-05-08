__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import sys, os

from PyQt4 import QtCore, QtGui

import orm

import wic
from wic import forms, w_app

appDir = os.path.dirname(os.path.abspath(__file__))


class App(w_app.WApp):

    def onSystemStarted(self): # предопределенная процедура запускаемая при начале работы системы - when the core is ready
        self.addCatalogActions(self.menu.catalogs)
        self.statusBar.showMessage('Ready...', 5000)
        # `<>` in the beginning of the string means to treat it as HTML
        self.printMessage('<><b><span style="color: green">Система запущена.</span> Добро пожаловать!</b>', True, False)
        print('Каталог приложения: %s' % appDir)

        global db
        db = orm.SqliteAdapter('papp/databases/mtc.sqlite')

#        from .reports.test import Form
#        forms.openForm(Form)
    #    
    #    from .reports.repayment_schedule import Form
    #    forms.openForm(Form)
    #    
    #    from .catalogs.books import Books
    #    book = Books.getOne(db, where= (Books.price > 14))
    #    print(db.getLastQuery())
    #
    #    openCatalogItemForm(book)
    #    openCatalogItemForm(Books(db))
    #    

#        openCatalogForm(Books, db)

        from .catalogs.locations import Locations
        forms.openCatalogForm(Locations, db)

        #self.mainWindow.restoreSubwindows()


    def onSystemAboutToExit(self): # предопределенная процедура запускаемая при завершении работы системы
        return True # return False to cancel quitting

    def addCatalogActions(self, menu):
        """Add actions for catalogs."""
        # http://docs.python.org/library/pkgutil.html#pkgutil.walk_packages
        from wic import menus
        catalogs = ('persons', 'locations', 'districts', 'regions', 'streets', 'new')
        for catalog in catalogs:
            modelName = catalog.capitalize()
            modelPath = 'papp.catalogs.' + catalog + '.' + modelName
            menus.addActionsToMenu(menu, (
                menus.createAction(menu, modelName, lambda *args, m = modelPath: self.openCatalogForm(m), icon = ':/icons/fugue/cards-stack.png'),
            ))
        
    def openCatalogForm(self, modelPath):
        from wic import getObjectByPath
        forms.openCatalogForm(getObjectByPath(modelPath), db)
    


def test():
    wic.app.showInformation('test', 'Это сообщение из процедуры "глобального" модуля')
