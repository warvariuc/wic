import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm
from ..locations import Location
from ..streets import Street


class Person(forms.catalog.CatalogModel):

    last_name = orm.CharField(max_length=50)
    first_name = orm.CharField(max_length=50)
    middle_name = orm.CharField(max_length=50)
    phone_prefix = orm.IntegerField(max_digits=3)
    phone_number = orm.IntegerField(max_digits=10)
    location = orm.RelatedRecordField(Location)
    street = orm.RelatedRecordField(Street)

    _meta = orm.ModelOptions(db_name='persons')

    def __str__(self):
        return self.last_name + ' ' + self.middle_name + ' ' + self.first_name
