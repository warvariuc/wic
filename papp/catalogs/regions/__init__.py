import os, sys
from PyQt4 import QtCore, QtGui

from wic import forms
import orm


class Regions(orm.Model):
    region_name = orm.CharField(maxLength= 50)
    region_type_name = orm.CharField(maxLength= 20)
