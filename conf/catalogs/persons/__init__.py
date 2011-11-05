import os, sys
from PyQt4 import QtCore, QtGui, uic

from wic.w import printMessage
from wic.form import WForm


class Form(WForm):
    ''''''

    @QtCore.pyqtSlot()
    def on_pushButton_clicked(self):
        # Using the same logic this slot is connected to the 'working' button
        # and only called once. The reason for this is that a lot of Qt signals
        # are overloaded, and if you dont specify which specific variant you
        # are interested in, then _all_ of them will be connected. Once way to
        # specify the specific signal is by use of the decorator above - in
        # this case, we will be connected to the signal with no arguments
        #
        # It is better explained in the documentation:
        # http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/pyqt4ref.html#connecting-slots-by-name
        print('!!!')
    

from wic import orm

class Persons(orm.Model):
    last_name = orm.StringField(maxLength= 100)
    first_name = orm.StringField(maxLength= 100)
    middle_name = orm.StringField(maxLength= 100)
    phone_prefix = orm.IntegerField(bytesCount= 2) # phone prefix code of the location
    phone_number = orm.IntegerField(bytesCount= 4)
    
    def checkNames(self):
        '''An item function, like in Django'''
        pass
    