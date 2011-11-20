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
from datetime import datetime as DateTime
from conf.catalogs.authors import Authors


class Books(orm.Model):
    name = orm.StringField(maxLength= 100, defaultValue= 'a very good book!!!')
    price = orm.fields.DecimalField(maxDigits= 10, fractionDigits= 2, defaultValue= '0.00', index= True)
    author_id = orm.RecordIdField(Authors, index= True)
    publication_date = orm.DateField()
    is_favorite = orm.BooleanField()

    def save(self):
        self._timestamp = None
        super().save()
