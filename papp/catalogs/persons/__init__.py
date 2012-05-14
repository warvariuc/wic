import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm
from ..locations import Locations
from ..streets import Streets


class Persons(forms.catalog.CatalogModel):
    last_name = orm.CharField(maxLength= 50)
    first_name = orm.CharField(maxLength= 50)
    middle_name = orm.CharField(maxLength= 50)
    phone_prefix = orm.IntegerField(maxDigits= 3)
    phone_number = orm.IntegerField(maxDigits= 10)
    location = orm.RecordField(Locations)
    street = orm.RecordField(Streets)

    def __str__(self):
        return self.last_name + ' ' + self.middle_name + ' ' + self.first_name
