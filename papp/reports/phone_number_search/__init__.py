

from PyQt5 import QtCore, QtGui, QtWidgets
from wic import forms
import orm


class Form(forms.WForm):

    _iconPath = ':/icons/fugue/telephone-handset-wire.png'

    def onOpen(self):
        """Called by the system after it loads the Form."""
        self.phoneNumber.returnPressed.connect(self.search.animateClick)
        self.lastName.returnPressed.connect(self.search.animateClick)
        self.searchResults.setColumnCount(2)
        self.searchResults.setHorizontalHeaderLabels(['Phone number', 'Name'])
        self.searchResults.resizeColumnsToContents()
        #self.searchResults.setStretchLastSection(True)

    @QtCore.pyqtSlot()
    def on_search_clicked(self):
        print('Search')
        phoneNumber = self._.phoneNumber.strip()
        lastName = self._.lastName.strip()
        if not phoneNumber and not lastName:
            self.showWarning('Bad data', 'Enter part of a phone number / last name.')
            return
        from papp.catalogs.persons import Persons
        from papp import db
        #print(list(Persons.get(db, where = (Persons.phone_number == phoneNumber), limit = 10, select_related = True)))
        where = None
        if phoneNumber:
            where = orm.CONCAT(Persons.phone_prefix, Persons.phone_number).LIKE('%' + phoneNumber + '%')
        if lastName:
            where2 = Persons.last_name.LIKE('%' + lastName + '%')
            where = where & where2 if where else where2
                
        items = Persons.get(db, where = where, limit = 100)
        
        if not items:
            self.showInformation('Nothing found', 'Nothing found')
            return
        
        self.searchResults.setRowCount(0)
        for item in items:
            rowNo = self.searchResults.rowCount()
            self.searchResults.insertRow(rowNo)
            self.searchResults.setItem(rowNo, 0, QtWidgets.QTableWidgetItem('%s-%s' % (item.phone_prefix, item.phone_number)))
            self.searchResults.setItem(rowNo, 1, QtWidgets.QTableWidgetItem('%s %s %s' % (item.last_name, item.first_name, item.middle_name)))
            
        self.searchResults.resizeColumnsToContents()
