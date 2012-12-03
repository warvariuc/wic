import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm

from ..regions import Regions


class Locations(forms.catalog.CatalogModel):
    location_name = orm.CharField(max_length= 50)
    location_type_name = orm.CharField(max_length= 50)
    region = orm.RelatedRecordField(Regions)

    def __str__(self):
        return self.location_name