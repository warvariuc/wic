import os, sys
from PyQt4 import QtCore, QtGui

from wic.forms import CatalogItemForm, setValue, getValue


#class Form(CatalogItemForm):
#    """"""
    #uiFilePath = 'form.ui' # auto generated form

#    def onOpen(self):
        #self.setWindowIcon(QtGui.QIcon(self.iconPath))
        #self.setWindowIcon(QtGui.QIcon(":/icons/calculator.png"))
        
#    def onSave(self):
#        super().onSave()
    
#    def on_descriptionSource_textChanged(self):
#        setValue(self.description, getValue(self.descriptionSource))

import orm
from datetime import datetime as DateTime
from conf.catalogs.authors import Authors


class Books(orm.Model):
    name = orm.CharField(maxLength= 100, defaultValue= 'a very good book!!!')
    price = orm.fields.DecimalField(maxDigits= 10, fractionDigits= 2, defaultValue= '0.00', index= True)
    author_id = orm.RecordIdField(Authors, index= True)
    publication_date = orm.DateField()
    description = orm.TextField()
    is_favorite = orm.BooleanField(label='Favorite')

#    def save(self):
#        self._timestamp = None
#        super().save()
