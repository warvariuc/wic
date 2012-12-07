import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm


class Region(forms.catalog.CatalogModel):

    region_name = orm.CharField(max_length=50)
    region_type_name = orm.CharField(max_length=20)

    _meta = orm.ModelOptions(db_name='regions')

    def __str__(self):
        return self.region_name
