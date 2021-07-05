import peewee

from PyQt5 import QtCore, QtGui, QtWidgets
from wic import forms


class Form(forms.Form):

    _icon_path = ':/icons/fugue/telephone-handset-wire.png'

    def on_open(self):
        """Called by the system after it loads the Form.
        """
        self.phoneNumber.returnPressed.connect(self.search.animateClick)
        self.lastName.returnPressed.connect(self.search.animateClick)
        self.searchResults.setColumnCount(2)
        self.searchResults.setHorizontalHeaderLabels(['Phone number', 'Name'])
        self.searchResults.resizeColumnsToContents()
        #self.searchResults.setStretchLastSection(True)

    @QtCore.pyqtSlot()
    def on_search_clicked(self):
        print('Search')
        phone_number = self._.phoneNumber.strip()
        last_name = self._.lastName.strip()
        if not phone_number and not last_name:
            self.show_warning('Bad data', 'Enter part of a phone number / last name.')
            return
        from app.catalogs.persons import Person
        from app import db
        #print(list(Persons.get(db, where = (Persons.phone_number == phoneNumber), limit = 10, select_related = True)))
        where = None
        if phone_number:
            where = orm.CONCAT(Person.phone_prefix, Person.phone_number).LIKE('%' + phone_number + '%')
        if last_name:
            where2 = Person.last_name.LIKE('%' + last_name + '%')
            where = where & where2 if where else where2
                
        items = Person.get(db, where = where, limit = 100)
        
        if not items:
            self.show_information('Nothing found', 'Nothing found')
            return
        
        self.searchResults.setRowCount(0)
        for item in items:
            rowNo = self.searchResults.row_count()
            self.searchResults.insertRow(rowNo)
            self.searchResults.setItem(rowNo, 0, QtWidgets.QTableWidgetItem(
                f'{item.phone_prefix}-{item.phone_number}'))
            self.searchResults.setItem(rowNo, 1, QtWidgets.QTableWidgetItem(
                f'{item.last_name} {item.first_name} {item.middle_name}'))
            
        self.searchResults.resizeColumnsToContents()
