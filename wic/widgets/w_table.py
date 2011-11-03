from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.widgets.w_date import Date
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit



class WTableItemProperties(): # data and flags for visual representation of an ItemView item/column; a kind of HTML style, that can be applied to any portion of text
    def __init__(self, format= '', editable= False, 
                alignment= None, defaultValue= None, roles= {}):
        self.format = format # text format of the value
        self.defaultValue = defaultValue
        if alignment is None:
            if isinstance(defaultValue, (Dec, int)): # by default decimals and integers are left aligned
                alignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            else:
                alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        self.roles = {QtCore.Qt.TextAlignmentRole: alignment} # alignment of the items from this item/column http://doc.trolltech.com/latest/qt.html#AlignmentFlag-enum
        for role, data in roles.items():
            self.roles[role] = data # todo: if data is a function use its return value as data
            
        self.flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        self.editable = editable
        
    def getEditable(self):
        return bool(~(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable) & self.flags)
    def setEditable(self, value):
        if value: self.flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable
        else: self.flags &= ~(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
    editable = property(getEditable, setEditable)
        
#        self.editFormat = ''


    def data(self, role, value): # http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
    
        if role == QtCore.Qt.DisplayRole:
            if isinstance(value, Date):
                return str(value)
            if isinstance(value, Dec):
                format_ = self.format
                if format_:
                    if format_[-1:] == ' ':
                        if value == 0:
                            return ''
                        format_ = format_[:-1]
                    return format(value, format_)
                else:
                    return str(value)
            elif isinstance(value, bool):
                return None # no text for checkboxes
            else:
                return value # todo: use self.format depending on value type
        elif role == QtCore.Qt.EditRole:
            return value
        elif role == QtCore.Qt.CheckStateRole:# or role == QtCore.Qt.EditRole:
            if isinstance(value, bool): # is boolean
                return QtCore.Qt.Checked if value else QtCore.Qt.Unchecked
        else:
            try: return self.roles[role]
            except: pass
        return None
    
    def flags(self): # http://doc.trolltech.com/latest/qt.html#ItemFlag-enum
        return self._flags
    


class WTableColumnProperties():
    def __init__(self, table, identifier, editedHandler, rowItem):
        self.table = table
        self.identifier = identifier
        self.headerItem = WTableItemProperties(alignment= QtCore.Qt.AlignCenter)
        self.rowItem = rowItem
        self.editedHandler = editedHandler
    
    def index(self):
        return self.table._columns.index(self)
        
    def getLabel(self): return self._label
    def setLabel(self, value):
        self._label = value # column header label
        if self.table._tableView:
            self.table._tableView.model().headerDataChanged.emit(QtCore.Qt.Horizontal, self.index(), self.index())
    label = property(getLabel, setLabel)
                
    def getWidth(self): 
        if self.table._tableView:
            return self.table._tableView.columnWidth(self.index())
    def setWidth(self, width):
        if self.table._tableView:
            self.table._tableView.setColumnWidth(self.index(), width)
    width = property(getWidth, setWidth)

    def getVisible(self): 
        if self.table._tableView:
            self.table._tableView.isColumnHidden(self.index)
    def setVisible(self, visibility):
        if self.table._tableView:
            self.table._tableView.setColumnHidden(self.index(), not visibility)
    visible = property(getVisible, setVisible)




class WTableRow(): # maybe subclass list instead of wrapping it?
    __slots__ = ['_table', '_values']
    def __init__(self, table):
        self._table = table
        self._values = []
        for column in self._table.columns():
            self._values.append(column.rowItem.defaultValue)

    def __setattr__(self, name, value):
        if name in WTableRow.__slots__:
            super().__setattr__(name, value)
            return
        try:
            self.__setitem__(name, value)
            return
        except KeyError: pass
        raise AttributeError('Неверное имя колонки')

    def __getattr__(self, name):
        try: return self._values[self._table._columnsOrder[name]]
        except KeyError: pass
        raise AttributeError('Неверное имя колонки')

    def index(self):
        return self._table._rows.index(self)
        
    def __getitem__(self, key):
        return self._values[self._table._columnsOrder[key] if isinstance(key, str) else key]

    def __setitem__(self, key, value):
        columnIndex = self._table._columnsOrder[key] if isinstance(key, str) else key 
        self._values[columnIndex] = value
        if self._table._tableView:
            tableModel = self._table._tableView.model()
            index = tableModel.index(self.index(), columnIndex)
            tableModel.dataChanged.emit(index, index)
            
    def values(self):
        return iter(self._values)




class WItemDelegate(QtGui.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        data = index.data(QtCore.Qt.EditRole)
        if isinstance(data, Date):
            editor = WDateEdit(parent)
            editor.value = data
            editor.edited.connect(self.commitAndCloseEditor)
            return editor
        if isinstance(data, Dec):
            editor = WDecimalEdit(parent)
            editor.value = data
            editor.edited.connect(self.commitAndCloseEditor)
            return editor
        return super().createEditor(parent, option, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, (WDateEdit, WDecimalEdit)):
            model.setData(index, editor.value)
        else:
            super().setModelData(editor, model, index)

    def commitAndCloseEditor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.NoHint)




class WTable(): # ТаблицаЗначений
    __slots__ = ['_columns', '_columnsOrder', '_rows', '_tableView']
    wItemDelegate = WItemDelegate() # static
    def __init__(self, tableView= None):
        self._columns = [] 
        self._rows = []
        self._columnsOrder = {} # column names and positions
        self.attachTableWidget(tableView)
    
    def attachTableWidget(self, tableView):
        if isinstance(tableView, QtGui.QTableView):
            self._tableView = tableView
            tableView.setModel(WTableModel(self))
            tableView.setItemDelegate(self.wItemDelegate)
        else:
            self._tableView = None
    
    def tableView(self): return self._tableView

    def rows(self): return iter(self._rows)
    def columns(self):  return iter(self._columns)

    def rowCount(self): return len(self._rows)
    def columnCount(self): return len(self._columnsOrder)

    def row(self, index): return self._rows[index]
    def column(self, key): 
        return self._columns[self._columnsOrder[key] if isinstance(key, str) else key]

    def _notifyTableView(self, end= False):
        if self._tableView: # notify about changes
            if end: self._tableView.model().layoutChanged.emit()
            else: self._tableView.model().layoutAboutToBeChanged.emit()

    def newRow(self, index= None):
        if not isinstance(index, int):
            index = self.rowCount()
        row = WTableRow(self)
        self._notifyTableView()
        self._rows.append(row)
        self._notifyTableView(True)
        return row
    
    def newColumn(self, identifier, index= None, label= '', width= 100, visible= True, editedHandler= None, **kwargs):
        if not identifier or (identifier in self._columnsOrder):
            raise AttributeError('Колонка с таким именем уже существует или не задано имя колонки: ' + identifier)
        if isinstance(index, str):
            try: index = self._columnsOrder[index]
            except KeyError: raise AttributeError('Колонка с таким именем не существует: ' + index)
        elif not isinstance(index, int):
            index = self.columnCount()
        
        column = WTableColumnProperties(self, identifier, editedHandler, WTableItemProperties(**kwargs))

        self._notifyTableView()
        self._columns.append(column)
        l = [''] * len(self._columnsOrder) # transform dict to list, insert new column and transform back
        for k, v in self._columnsOrder.items(): l[v] = k
        l.insert(index, identifier)
        for i, v in enumerate(l): self._columnsOrder[v] = i
        
        for row in self._rows:
            row._values.insert(index, None)

        column.label = label if label else identifier # column header label
        column.visible = visible
        column.width = width
        self._notifyTableView(True)
        
        return column

    def delRow(self, rowIndex):
        self._notifyTableView()
        del self._rows[rowIndex]
        self._notifyTableView(True)
        
    def delColumn(self, columnIndex):
        self._notifyTableView()
        for row in self._rows:
            del row._values[columnIndex]
        self._notifyTableView(True)
        
    def delRows(self):
        self._notifyTableView()
        self._rows = []
        self._notifyTableView(True)
        
    def getValue(self, rowIndex, columnIndex):
        return self._rows[rowIndex][columnIndex]
        
    def setValue(self, rowIndex, columnIndex, value):
        self._rows[rowIndex][columnIndex] = value
        
    def copy(self):
        table = WTable()
        for column in self._columns: # todo: copy visual properties
            table.newColumn(column.identifier)
        for row in self._rows:
            newRow = table.newRow()
            newRow._values = row._values[:]
        return table



class WTableModel(QtCore.QAbstractTableModel):
    def __init__(self, wTable):
        super().__init__(None) # no parent
        self.wTable = wTable

    def rowCount(self, parent):
        return self.wTable.rowCount()

    def columnCount(self, parent):
        return self.wTable.columnCount()

    def data(self, index, role):
        if not index.isValid():  return None
        value = self.wTable.getValue(index.row(), index.column())
        return self.wTable.column(index.column()).rowItem.data(role, value)

    def setData(self, index, value, role=QtCore.Qt.EditRole): # editable model - data may be edited through an item delegate editor (WDateEdit, WDecimalEdit, QLineEdit, etc.)
        if index.isValid():
            if role == QtCore.Qt.CheckStateRole:
                value = True if value == QtCore.Qt.Checked else False
                role = QtCore.Qt.EditRole # reuse the code
            if role == QtCore.Qt.EditRole:
                row = self.wTable.row(index.row())
                row[index.column()] = value
                self.dataChanged.emit(index, index)
                column = self.wTable.column(index.column())
                if column.editedHandler: 
                    try: column.editedHandler(row, column, value)
                    except Exception as err: print(str(err))
                return True
        return False

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self.wTable.column(section).label
            else:
                return self.wTable.column(section).headerItem.data(role, None)
        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return str(section) # for rows display row number
        return None

    def flags(self, index):
        if not index.isValid(): 
            return QtCore.Qt.ItemIsEnabled
        return self.wTable.column(index.column()).rowItem.flags
            




if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])
    
    tableView = QtGui.QTableView(None)
    
    table = WTable(tableView)
    table.newColumn("column1", label= 'int', defaultValue= 0, width= 50)
    table.newColumn("column2", label= 'Decimal', editable= True, alignment= QtCore.Qt.AlignRight, defaultValue= Dec())
    table.newColumn("column3", label= 'Date', editable= True, defaultValue= Date())
    for rowIndex in range(10):
        row = table.newRow()
        row.column1 = rowIndex + 1
        row.column2 = Dec(rowIndex)
    
    tableView.show()
    app.exec()