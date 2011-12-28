import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm
from ..locations import Locations
from ..streets import Streets


class Persons(orm.Model):
    last_name = orm.CharField(maxLength= 50)
    first_name = orm.CharField(maxLength= 50)
    middle_name = orm.CharField(maxLength= 50)
    phone_prefix = orm.IntegerField(maxDigits= 3)
    phone_number = orm.IntegerField(maxDigits= 10)
    location_id = orm.RecordIdField(Locations)
    street_id = orm.RecordIdField(Streets)
