import os, sys
from PyQt4 import QtCore, QtGui

from wic.w import printMessage
from wic.forms import CatalogForm


class Form(CatalogForm):
    ''''''
    uiFilePath = '' # auto generated form

    @QtCore.pyqtSlot()
    def on_pushButton_clicked(self):
        print('!!!')
        
    #def on_open(self):
        #self.setWindowIcon(QtGui.QIcon(self.iconPath))
        #self.setWindowIcon(QtGui.QIcon(":/icons/calculator.png"))    



import orm

class Authors(orm.Model):
    first_name = orm.CharField(maxLength= 100)
    last_name = orm.CharField(maxLength= 100)
