import os, sys
from PyQt4 import QtCore, QtGui

import orm
from wic import forms



class Users(forms.catalog.CatalogModel):
    name = orm.CharField(max_length=20)
    full_name = orm.CharField(max_length=50)
    password_hash = orm.CharField(max_length=32)
    is_enabled = orm.BooleanField()


class Form(forms.CatalogItemForm):
    """"""

    @QtCore.pyqtSlot()
    def on_buttonTestConnection_clicked(self):
        dbUri = forms._.dbUri
        import orm
        ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters
        try: # 'sqlite://../mtc.sqlite'
            db = orm.connect(dbUri, ADAPTERS)
            if db is None:
                raise orm.ConnectionError('Could not find suitable DB adapter for the protocol specified.')
            db.execute('SELECT 1;')
        except Exception as exc:
            QtGui.QMessageBox.warning(self, 'Failure', '<b>Connection failure</b><br>%s\n%s' % (dbUri, exc))
        else:
            QtGui.QMessageBox.information(self, 'Success', '<b>Connection success</b><br>%s' % dbUri)
        
    def on_buttonBox_accepted(self):
        print('accepted')
        
    #def on_open(self):
        #self.setWindowIcon(QtGui.QIcon(self._iconPath))
        #self.setWindowIcon(QtGui.QIcon(":/icons/calculator.png"))    




import hashlib
hashlib.md5("Nobody inspects the spammish repetition".encode()).hexdigest()
