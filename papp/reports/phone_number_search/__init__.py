__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from PyQt4 import QtCore, QtGui
from wic import forms
import orm


class Form(forms.WForm):

    _iconPath = ':/icons/fugue/telephone-handset-wire.png'

    def onOpen(self):
        """Called by the system after it loads the Form."""
        self.phoneNumber.returnPressed.connect(self.search.animateClick)
        self.lastName.returnPressed.connect(self.search.animateClick)

    @QtCore.pyqtSlot()
    def on_search_clicked(self):
        print('Search')
        phoneNumber = self._.phoneNumber.strip()
        lastName = self._.lastName.strip()
        if not phoneNumber and not lastName:
            self.showWarning('Bad data', 'Enter part of a phone number or part of a last name.')
            return
        from papp.catalogs.persons import Persons
        from papp import db
        #print(list(Persons.get(db, where = (Persons.phone_number == phoneNumber), limit = 10, select_related = True)))
        combinedPhoneNumber = orm.CONCAT(Persons.phone_prefix, Persons.phone_number)
        print(db._select('*', combinedPhoneNumber, from_ = Persons, where = combinedPhoneNumber.LIKE('%' + phoneNumber + '%'), limit = 10))
