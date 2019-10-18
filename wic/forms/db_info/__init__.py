import os, sys
from PyQt5 import QtCore, QtGui, QtWidgets

from wic import forms


class Form(forms.WForm):
    """"""

    @QtCore.pyqtSlot()
    def on_buttonTestConnection_clicked(self):
        dbUri = self._.dbUri
        import orm
        ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters
        try: # 'sqlite://../mtc.sqlite'
            db = orm.connect(dbUri, ADAPTERS)
            if db is None:
                raise orm.ConnectionError('Could not find suitable DB adapter for the protocol specified.')
            db.execute('SELECT 1;')
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, 'Failure', '<b>Connection failure</b><br>%s\n%s' % (dbUri, exc))
        else:
            QtWidgets.QMessageBox.information(self, 'Success', '<b>Connection success</b><br>%s' % dbUri)
        
    def on_buttonBox_accepted(self):
        print('accepted')
        
    #def on_open(self):
        #self.setWindowIcon(QtGui.QIcon(self._iconPath))
        #self.setWindowIcon(QtGui.QIcon(":/icons/calculator.png"))    




