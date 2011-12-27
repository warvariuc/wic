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
from ..authors import Authors


class Locations(orm.Model):
    location_name = orm.CharField(maxLength= 50)
    location_type_name = orm.CharField(maxLength= 50)
    region_id = orm.IntegerField()
