import os, sys
from PyQt4 import QtCore, QtGui

from wic.w import printMessage
from wic.forms import WForm, getValue


class Form(WForm):
    ''''''

    @QtCore.pyqtSlot()
    def on_buttonTestConnection_clicked(self):
        dbUri = getValue(self.dbUri)
        from wic import orm
        ADAPTERS = dict(sqlite= orm.SqliteAdapter, mysql= orm.MysqlAdapter) # available adapters
        try: # 'sqlite://../mtc.sqlite'
            db = orm.connect(dbUri, ADAPTERS)
            if db is None:
                raise orm.ConnectionError('Could not find suitable DB adapter for the protocol specified.')
            db.execute('SELECT 1;')
        except orm.ConnectionError as exc:
            QtGui.QMessageBox.warning(self, 'Failure', 'Connection failure:\n%s' % exc)
        else:
            QtGui.QMessageBox.information(self, 'Success', 'The connection was successfully tested.')
        
    def on_buttonBox_accepted(self):
        print('accepted')
        
    #def on_open(self):
        #self.setWindowIcon(QtGui.QIcon(self.iconPath))
        #self.setWindowIcon(QtGui.QIcon(":/icons/calculator.png"))    



#from PyQt4 import QtGui, QtSql
#import os
#import w
#
#class DbInfo():
#    def __init__(self, dirPath):
#        self.identifier = ''
#        self.filePath = os.path.join(dirPath, 'db_info.yaml')
#        self.data = w.loadFromFile(self.filePath)
#            
#    def edit(self, parentWidget):
#        dialog = w.putToForm(self.data, os.path.join(QtGui.qApp.appDir, 'forms', 'db_info.ui'), parentWidget)
#        dialog.db_driver_name.addItems(QtSql.QSqlDatabase.drivers())
#        
#        dialog.buttonBox.accepted.connect(lambda d=dialog: self.checkAccept(d))
#        dialog.exec()
#
#    def checkAccept(self, dialog): #check the data and accept it if OK
#        self.data.update(w.getFromForm(dialog))
#        dialog.accept()
#        w.saveToFile(self.data, self.filePath)
#        createConnection(self)
#
#
#def createConnection(dbInfo=None): # loads connection requisites from yaml file and creates default connection
#    dbInfo = dbInfo or DbInfo(QtGui.qApp.confDir)
#
#    db_name = dbInfo.data['db_name']
#    db_driver_name = dbInfo.data['db_driver_name']
#    if db_driver_name == 'QSQLITE':
#        if not os.path.isabs(db_name):
#            db_name = os.path.join(QtGui.qApp.confDir, db_name)
#
#    db = QtSql.QSqlDatabase.addDatabase(db_driver_name, '') # empty database name - creates default application connection
#    db.setDatabaseName(db_name) # The database name is not the connection name.
#
#    if db.open():
##        tables = db.tables(QtSql.QSql.Tables)
##        print(tables)
##        for table_name in tables[1:]:
##            table_model = QtSql.QSqlTableModel(None, db)
##            table_model.setTable(table_name)
##            print(table_model.tableName())
##            record = QtSql.QSqlRecord(table_model.record()) # Returns an empty record containing information about the fields of the current query.
##            for i in range (record.count()):
##                field = record.field(i)
##                print(field.name(), field.type(), field.length(), field.precision())
#        return True
#    else:
#        print ("Ошибка при подключении БД")
#        print (db.lastError().text())
#        return False
#
