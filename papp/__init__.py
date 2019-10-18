__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import sys, os

# from PyQt5 import QtCore, QtGui

import orm

import wic
from wic import forms, w_main_window

appDir = os.path.dirname(os.path.abspath(__file__))
db = None


class MainWindow(w_main_window.WMainWindow):

    def onSystemStarted(self): # predefined function scalled when the core is ready
        self.statusBar().showMessage('Ready...', 5000)
        # `<>` in the beginning of the string means to treat it as HTML
        self.printMessage('<><b><span style="color: green">System started.</span> Welcome!</b>', True, False)
        print('Application directory: %s' % appDir)

        global db
        db = orm.SqliteAdapter('papp/databases/mtc.sqlite')

        from .reports import phone_number_search
        forms.openForm(phone_number_search.Form)
        #self.mainWindow.restoreSubwindows()

    def onSystemAboutToExit(self): # предопределенная процедура запускаемая при завершении работы системы
        return True # return False to cancel quitting

    def setupMenu(self):
        super().setupMenu()

        #Add actions for catalogs.
        # http://docs.python.org/library/pkgutil.html#pkgutil.walk_packages
        menu = self.menu.catalogs
        from wic import menus
        catalogs = ('persons', 'locations', 'districts', 'regions', 'streets')
        for catalog in catalogs:
            modelName = catalog.capitalize()
            modelPath = 'papp.catalogs.' + catalog + '.' + modelName
            menus.addActionsToMenu(menu, (
                menus.createAction(menu, modelName, lambda *args, p = modelPath: forms.openCatalogForm(p, db),
                                   icon = ':/icons/fugue/cards-address.png'),
            ))

        menu = self.menu.reports
        reports = ('phone_number_search', 'test', 'lissajous', 'repayment_schedule')
        for report in reports:
            reportName = report.capitalize()
            reportPath = 'papp.reports.' + report + '.Form'
            menus.addActionsToMenu(menu, (
                menus.createAction(menu, reportName, lambda *args, p = reportPath: forms.openForm(p),
                                   icon = ':/icons/fugue/application-form.png'),
            ))


def test():
    wic.app.showInformation('test', 'Это сообщение из процедуры "глобального" модуля')
