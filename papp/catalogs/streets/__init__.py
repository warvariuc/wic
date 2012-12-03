from PyQt4 import QtCore, QtGui

from wic import forms
import orm
from ..locations import Locations


class Streets(forms.catalog.CatalogModel):
    street_name = orm.CharField(max_length= 50)
    street_old_name = orm.CharField(max_length= 50)
    street_type_name = orm.CharField(max_length= 20)
    location = orm.RelatedRecordField(Locations)

    def __str__(self):
        return self.street_name or ''
