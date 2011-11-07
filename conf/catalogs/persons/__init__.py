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

from wic import orm

class Persons(orm.Model):
    last_name = orm.fields.StringField(maxLength= 100)
    first_name = orm.StringField(maxLength= 100)
    middle_name = orm.StringField(maxLength= 100)
    phone_prefix = orm.IntegerField(bytesCount= 2) # phone prefix code of the location
    phone_number = orm.IntegerField(bytesCount= 4)
    
    def getFullName(self):
        '''An item function, like in Django'''
        return '%s %s %s' % (self.last_name, self.first_name, self.middle_name)
    