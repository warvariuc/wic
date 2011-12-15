from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.datetime import Date
import traceback

import orm

from wic.w_table import WItemStyle

from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit




class Cache():
    '''Cache for keeping query results from DB'''
    def __init__(self, db, catalogModel, where):
        self.db = db
        self.catalogModel = catalogModel
        self.where = where
        self.expireTime = 3 # in seconds
        self._rowsCount = None
        self.countStart = 0
        self.countEnd = 0
        self.rows = db.select(catalogModel, where= where)[1]
        
    def rowsCount(self):
        ''
        if self._rowsCount is None:
            self._rowsCount = self.catalogModel.count(self.db)
        return self._rowsCount
    
    def item(self, rowNo, columnNo):
        ''
        return self.rows[rowNo][columnNo]

    def fetch(self):
        'Fetch chunk of results of the query'
        
    def expire(self):
        'Set the cache as expired'
        

def createStyleForField(field):
    assert isinstance(field, orm.Field)
    if isinstance(field, orm.DecimalField):
        # align decimals and integers to right
        return WItemStyle(format= ',.%if ' % field.fractionDigits, 
                            roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight})
    else:
        return WItemStyle(roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft})
        
#
#    
#    if isinstance(field, (orm.CharField, orm.IntegerField, orm.IdField, orm.RecordIdField, orm.DateTimeField)):
#        return QtGui.QLineEdit()
#    elif isinstance(field, orm.DecimalField):
#        return WDecimalEdit()
#    elif isinstance(field, orm.DateField):
#        return WDateEdit()
#    elif isinstance(field, orm.BooleanField):
#        return QtGui.QCheckBox(field.name)
#    elif isinstance(field, orm.TextField):
#        return QtGui.QPlainTextEdit()
#    raise Exception('Could not create a widget for field %s' % field)



class WCatalogModel(QtCore.QAbstractTableModel):
    '''Model for showing list of catalog items.'''

    def __init__(self, db, catalogModel, where= None):
        assert orm.isModel(catalogModel)
        super().__init__(None) # no parent
        self._cache = Cache(db, catalogModel, where)
        self._columnNames = []
        self._columnStyles = []
        for field in catalogModel:
            self._columnNames.append(field.name)
            self._columnStyles.append(createStyleForField(field))


    def rowCount(self, parent):
        return self._cache.rowsCount()

    def columnCount(self, parent):
        return len(self._columnNames)

    def data(self, index, role):
        if index.isValid():
            value = self._cache.item(index.row(), index.column())
            return self._columnStyles[index.column()].data(role, value)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self._columnNames[section] #self.wTable.column(section).label
        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return str(section) # for rows display row number
        return None

    def eventFilter(self, tableView, event): # target - tableView
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if event.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
                if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    if tableView.state() != tableView.EditingState:
                        index = tableView.currentIndex()
                        if tableView.model().flags(index) & QtCore.Qt.ItemIsEditable:
                            tableView.edit(index)
                            return True
        return super().eventFilter(tableView, event) # standard event processing        

#    def setQuery(self, model, fields):
#        ''''''
#        assert isinstance(model, orm.Model), 'Pass an orm.Model instance'
#        assert all(isinstance(field, orm.Field) for field in fields), 'All fields must be instances of orm.Field'





if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])

    tableView = QtGui.QTableView(None)

    table = WTable(tableView)
    table.newColumn('column1', label = 'int', default = 0, width = 50)
    table.newColumn('column2', label = 'Decimal', editable = True, alignment = QtCore.Qt.AlignRight, default = Dec())
    table.newColumn('column3', label = 'Date', editable = True, default = Date())
    for rowIndex in range(10):
        row = table.newRow()
        row.column1 = rowIndex + 1
        row.column2 = Dec(rowIndex)

    tableView.show()
    app.exec()
