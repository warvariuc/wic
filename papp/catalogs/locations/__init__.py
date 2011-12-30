import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms



import orm

from ..regions import Regions


class Locations(forms.catalog.CatalogModel):
    location_name = orm.CharField(maxLength= 50)
    location_type_name = orm.CharField(maxLength= 50)
    region_id = orm.RecordIdField(Regions)
