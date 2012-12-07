import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm
from ..locations import Location


class District(forms.catalog.CatalogModel):

    localitate = orm.CharField(max_length=100)
    judet = orm.CharField(max_length=50)
    raion = orm.CharField(max_length=50)
    prefix = orm.IntegerField(max_digits=10)
    posta = orm.CharField(max_length=20)
    comuna = orm.CharField(max_length=50)

    _meta = orm.ModelOptions(db_name='districts')

#    def __str__(self):
#        return self.judet + ' ' + self
