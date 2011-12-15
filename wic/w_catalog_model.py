from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.datetime import Date, _format as formatDate
import traceback

import orm

from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit



class WColumnStyle():
    'Data and flags for visual representation of a QTableView column.'

    def __init__(self, format = '', alignment = None, roles = None):
        self.format = format # text format of the value
        self.roles = roles or {}

        self.flags = QtCore.Qt.ItemIsSelectable # QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def isEditable(self):
        return bool(~(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable) & self.flags)
    def setEditable(self, value):
        if value:
            self.flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable
        else:
            self.flags &= ~(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
    editable = property(isEditable, setEditable)


    def data(self, role, value): # http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
        if role == QtCore.Qt.DisplayRole:
            if isinstance(value, Date):
                return formatDate(value)
            if isinstance(value, Dec):
                _format = self.format
                if _format:
                    if _format[-1:] == ' ':
                        if value == 0:
                            return ''
                        _format = _format[:-1]
                    return format(value, _format)
                else:
                    return str(value)
            elif isinstance(value, bool):
                return None # no text for checkboxes
            else:
                return value # TODO: use self.format depending on value type
        elif role == QtCore.Qt.EditRole:
            return value
        elif role == QtCore.Qt.CheckStateRole:# or role == QtCore.Qt.EditRole:
            if isinstance(value, bool): # is boolean
                return QtCore.Qt.Checked if value else QtCore.Qt.Unchecked
        return self.roles.get(role)

    def flags(self): # http://doc.trolltech.com/latest/qt.html#ItemFlag-enum
        return self._flags



class WTableColumnProperties():
    def __init__(self, table, identifier, onEdited, rowItem):
        self.table = table
        self.identifier = identifier
        self.headerItem = WTableItemProperties(alignment = QtCore.Qt.AlignCenter)
        self.rowItem = rowItem
        self.onEdited = onEdited

    def index(self):
        return self.table._columns.index(self)

    def label(self): return self._label
    def setLabel(self, value):
        self._label = value # column header label
        if self.table._tableView:
            self.table._tableView.model().headerDataChanged.emit(QtCore.Qt.Horizontal, self.index(), self.index())
    label = property(label, setLabel)

    def width(self):
        if self.table._tableView:
            return self.table._tableView.columnWidth(self.index())
    def setWidth(self, width):
        if self.table._tableView:
            self.table._tableView.setColumnWidth(self.index(), width)
    width = property(width, setWidth)

    def isVisible(self):
        if self.table._tableView:
            self.table._tableView.isColumnHidden(self.index)
    def setVisible(self, visibility):
        if self.table._tableView:
            self.table._tableView.setColumnHidden(self.index(), not visibility)
    visible = property(isVisible, setVisible)




class Cache():
    '''Cache for keeping query results from DB'''
    def __init__(self, db, catalogModel):
        self.catalogModel = catalogModel
        self.db = db
        self.expireTime = 3 # in seconds
        self._rowsCount = None
        self.countStart = 0
        self.countEnd = 0
        
    def getRowsCount(self):
        ''
        if self._rowsCount is None:
            self._rowsCount = self.catalogModel.count(self.db)
        return self._rowsCount
    
    rowsCount = property(getRowsCount)
    

    def fetch(self):
        'Fetch chunk of results of the query'
        
    def expire(self):
        'Set the cache as expired'


def createStyleForField(field):
    assert isinstance(field, orm.Field)
    if isinstance(field, orm.DecimalField):
        # align decimals and integers to right
        return WColumnStyle(format= ',.%if ' % field.fractionDigits, 
                            roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight})
    else:
        return WColumnStyle(roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft})
        
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
        self.catalogModel = catalogModel
        self.db = db
        self._cache = Cache(db, catalogModel)
        self._columnNames = []
        self._columnStyles = []
        for field in catalogModel:
            self._columnNames.append(field.name)
            self._columnStyles.append(createStyleForField(field))


    def rowCount(self, parent):
        return self._cache.rowsCount

    def columnCount(self, parent):
        return len(self._columnNames)

    def data(self, index, role):
        if index.isValid():
            value = Dec('12.135') # self.wTable.getValue(index.row(), index.column())
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

    def _fetch(self):
        ''''''

    def setQuery(self, model, fields):
        ''''''
        assert isinstance(model, orm.Model), 'Pass an orm.Model instance'
        assert all(isinstance(field, orm.Field) for field in fields), 'All fields must be instances of orm.Field'





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
