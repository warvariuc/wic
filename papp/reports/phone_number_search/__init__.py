__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from PyQt4 import QtCore, QtGui
from wic import forms


class Form(forms.WForm):

    _iconPath = ':/icons/fugue/telephone-handset-wire.png'

    def onOpen(self):
        """Called by the system after it loads the Form."""

    @QtCore.pyqtSlot()
    def on_search_clicked(self):
        print('Search')
