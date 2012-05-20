__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import sys, os

from PyQt4 import QtCore, QtGui

import orm

import wic
from wic import forms, w_main_window

appDir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(w_main_window.WMainWindow):

    def onSystemStarted(self): # predefined function scalled when the core is ready
        self.statusBar().showMessage('Ready...', 5000)
        # `<>` in the beginning of the string means to treat it as HTML
        self.printMessage('<><b><span style="color: green">System started.</span> Welcome!</b>', True, False)
        print('Application directory: %s' % appDir)

        global db
        db = orm.SqliteAdapter('papp/databases/mtc.sqlite')

#        from .reports.test import Form
#        forms.openForm(Form)
    #    
    #    from .reports.repayment_schedule import Form
    #    forms.openForm(Form)
    #    
        from .catalogs.locations import Locations
        forms.openCatalogForm(Locations, db)

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
                menus.createAction(menu, modelName, lambda *args, m = modelPath: self.openCatalogForm(m), 
                                   icon = ':/icons/fugue/cards-address.png'),
            ))
            
        menu = self.menu.reports = self.menu.addMenu('Reports')
        reports = ('test', 'lissajous', 'repayment_schedule')
        for report in reports:
            reportName = report.capitalize()
            reportPath = 'papp.reports.' + report + '.Form'
            menus.addActionsToMenu(menu, (
                menus.createAction(menu, reportName, lambda *args, p = reportPath: self.openReportForm(p), 
                                   icon = ':/icons/fugue/application-form.png'),
            ))

    def openCatalogForm(self, modelPath):
        from wic import getObjectByPath
        forms.openCatalogForm(getObjectByPath(modelPath), db)

    def openReportForm(self, reportPath):
        from wic import getObjectByPath
        forms.openForm(getObjectByPath(reportPath))


def test():
    wic.app.showInformation('test', 'Это сообщение из процедуры "глобального" модуля')
