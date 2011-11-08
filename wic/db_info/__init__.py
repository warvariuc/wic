import os, sys
from PyQt4 import QtCore, QtGui

from wic.w import printMessage
from wic.forms import WForm, getValue


class Form(WForm):
    ''''''

    @QtCore.pyqtSlot()
    def on_buttonTestConnection_clicked(self):
        dbUri = getValue(self.dbUri)
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
        #self.setWindowIcon(QtGui.QIcon(self.iconPath))
        #self.setWindowIcon(QtGui.QIcon(":/icons/calculator.png"))    




