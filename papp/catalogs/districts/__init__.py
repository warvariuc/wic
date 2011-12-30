import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm
from ..locations import Locations


class Districts(forms.catalog.CatalogModel):
    localitate = orm.CharField(maxLength= 100)
    judet = orm.CharField(maxLength= 50)
    raion = orm.CharField(maxLength= 50)
    prefix = orm.IntegerField(maxDigits= 10)
    posta = orm.CharField(maxLength= 20)
    comuna = orm.CharField(maxLength= 50)
