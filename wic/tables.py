from decimal import Decimal

from PyQt5 import QtGui, QtCore, QtWidgets

from wic.datetime import Date, format as format_date
from wic.widgets import DateEdit, DecimalEdit


class ItemStyle():
    """Data and flags for visual representation of an ItemView item
    """
    def __init__(self, format='', editable=False,
                alignment=None, default=None, roles=None):
        self.format = format # text format of the value
        self.default = default
        if alignment is None:
            if isinstance(default, (Decimal, int)): # by default decimals and integers are left aligned
                alignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            else:
                alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        self.roles = {QtCore.Qt.TextAlignmentRole: alignment} # alignment of the items from this item/column: http://doc.trolltech.com/latest/qt.html#AlignmentFlag-enum
        self.roles.update(roles or {})

        self.flags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        self.editable = editable

    def isEditable(self):
        return bool(~self.flags & QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
    def setEditable(self, value):
        if value:
            self.flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable
        else:
            self.flags &= ~(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable)
    editable = property(isEditable, setEditable)

    def data(self, role, value):
        # http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
        if role == QtCore.Qt.DisplayRole:
            if isinstance(value, Date):
                return format_date(value)
            if isinstance(value, Decimal):
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
                return None  # no text for checkboxes
            else:
                return value  # TODO: use self.format depending on value type
        elif role == QtCore.Qt.EditRole:
            return value
        elif role == QtCore.Qt.CheckStateRole:# or role == QtCore.Qt.EditRole:
            if isinstance(value, bool): # is boolean
                return QtCore.Qt.Checked if value else QtCore.Qt.Unchecked
        return self.roles.get(role)

    # def flags(self):  # http://doc.trolltech.com/latest/qt.html#ItemFlag-enum
    #     return self._flags


class TableColumnProperties():
    def __init__(self, table, identifier, on_edited, row_item):
        self.table = table
        self.identifier = identifier
        self.header_item = ItemStyle(alignment=QtCore.Qt.AlignCenter)
        self.row_item = row_item
        self.on_edited = on_edited

    def index(self):
        return self.table._columns.index(self)

    def label(self):
        return self._label
    def setLabel(self, value):
        self._label = value  # column header text
        if self.table._table_view:
            self.table._table_view.model().headerDataChanged.emit(
                QtCore.Qt.Horizontal, self.index(), self.index())
    label = property(label, setLabel)

    def width(self):
        if self.table._table_view:
            return self.table._table_view.columnWidth(self.index())
    def setWidth(self, width):
        if self.table._table_view:
            self.table._table_view.setColumnWidth(self.index(), width)
    width = property(width, setWidth)

    def isVisible(self):
        if self.table._table_view:
            return self.table._table_view.isColumnHidden(self.index)
    def setVisible(self, visibility):
        if self.table._table_view:
            self.table._table_view.setColumnHidden(self.index(), not visibility)
    visible = property(isVisible, setVisible)


class TableRow():
    # maybe subclass list instead of wrapping it?
    __slots__ = ['_table', '_values']
    def __init__(self, table, from_row=None):
        self._table = table
        self._values = from_row._values[:] if from_row else []
        for column in self._table.columns():
            self._values.append(column.row_item.default)

    def __setattr__(self, name, value):
        if name in TableRow.__slots__:
            return super().__setattr__(name, value)
        try:
            return self.__setitem__(name, value)
        except KeyError:
            pass
        raise AttributeError(f'Invalid column name: {name}')

    def __getattr__(self, name):
        try:
            return self._values[self._table._columns_order[name]]
        except KeyError:
            pass
        raise AttributeError(f'Invalid column name: {name}')

    def index(self):
        return self._table._rows.index(self)

    def __getitem__(self, key):
        return self._values[self._table._columns_order[key] if isinstance(key, str) else key]

    def __setitem__(self, key, value):
        column_index = self._table._columns_order[key] if isinstance(key, str) else key
        self._values[column_index] = value
        if self._table._table_view:
            table_model = self._table._table_view.model()
            index = table_model.index(self.index(), column_index)
            table_model.dataChanged.emit(index, index)

    def values(self):
        return self._values


class ItemDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        data = index.data(QtCore.Qt.EditRole)
        if isinstance(data, Date):
            editor = DateEdit(parent)
            editor.setDate(data)
            editor.edited.connect(self.commit_and_close_editor)
            # FIXME: editor.edited.connect(lambda e=editor: self.commitAndCloseEditor(e))
            return editor
        if isinstance(data, Decimal):
            editor = DecimalEdit(parent)
            editor.setValue(data)
            editor.edited.connect(self.commit_and_close_editor)
            return editor
        return super().createEditor(parent, option, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, DateEdit):
            model.setData(index, editor.date())
        elif isinstance(editor, DecimalEdit):
            model.setData(index, editor.value())
        else:
            super().setModelData(editor, model, index)

    def commit_and_close_editor(self):
        editor = self.sender()
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QtWidgets.QAbstractItemDelegate.NoHint)


class Table():
    """A two-dimensional table with names columns.
    Can be attached to a table view.
    """

    __slots__ = ['_columns', '_columns_order', '_rows', '_table_view']

    item_delegate = ItemDelegate()

    def __init__(self, table_view=None):
        assert table_view is None or isinstance(table_view, QtWidgets.QTableView), \
            'Pass a QtGui.QTableView'
        super().__init__()
        self._columns = []
        self._rows = []
        self._columns_order = {}  # column names and positions
        self._table_view = None
        self.attach_table_view(table_view)

    def attach_table_view(self, table_view):
        """Attach this table to an existing table view.

        Args:
            table_view (QTableView): instance to which to attach or None - to release
        """
        if not table_view:
            if self._table_view:
                self._table_view.removeEventFilter(self._table_view.model())
            self._table_view = None
        else:
            table_view.setModel(TableModel(self))
            table_view.setItemDelegate(self.item_delegate)
            table_view.installEventFilter(table_view.model())  # for hooking Enter key
            self._table_view = table_view

    def table_view(self):
        return self._table_view

    def rows(self):
        return self._rows

    def columns(self):
        return self._columns

    def row_count(self):
        return len(self._rows)

    def column_count(self):
        return len(self._columns_order)

    def row(self, index):
        return self._rows[index]

    def column(self, key):
        """Get column by index or name

        Args:
            key (int|str): column index or its name
        """
        return self._columns[self._columns_order[key] if isinstance(key, str) else key]

    def _notify_table_view(self, end=False):
        if self._table_view:  # notify about changes
            if end:
                self._table_view.model().layoutChanged.emit()
            else:
                self._table_view.model().layoutAboutToBeChanged.emit()

    def new_row(self, index=None, from_row=None):
        """Add new row to the table.

        Args:
            index (Optional[int]): at which index; if not given, the row is inserted at the end
            from_row (Optional[TableRow]): if given, values from this row will copied to the new
                one

        Returns:
            TableRow: the new row
        """
        if not isinstance(index, int):
            index = self.row_count()
        row = TableRow(self, from_row=from_row)
        self._notify_table_view()
        self._rows.insert(index, row)
        self._notify_table_view(True)
        return row

    def new_column(
            self, identifier, index=None, label='', width=100, visible=True, on_edited=None,
            **kwargs
    ):
        if identifier in self._columns_order:
            raise AttributeError(f'Column with name `{identifier}` already exists.')
        if isinstance(index, str):
            try:
                index = self._columns_order[index]
            except KeyError:
                raise AttributeError(f'Column with name `{index}` does not exist.')
        elif not isinstance(index, int):
            index = self.column_count()

        column = TableColumnProperties(self, identifier, on_edited, ItemStyle(**kwargs))

        self._notify_table_view()
        self._columns.append(column)
        # transform dict to list, insert new column and transform back
        l = [''] * len(self._columns_order)
        for k, v in self._columns_order.items():
            l[v] = k
        l.insert(index, identifier)
        for i, v in enumerate(l):
            self._columns_order[v] = i

        for row in self._rows:
            row._values.insert(index, None)

        column.label = label or identifier  # column header label
        column.visible = visible
        column.width = width
        self._notify_table_view(True)

        return column

    def delRow(self, row_index):
        self._notify_table_view()
        del self._rows[row_index]
        self._notify_table_view(True)

    def delColumn(self, column_index):
        self._notify_table_view()
        for row in self._rows:
            del row._values[column_index]
        self._notify_table_view(True)

    def delRows(self):
        self._notify_table_view()
        self._rows = []
        self._notify_table_view(True)

    def getValue(self, row_index, column_index):
        return self._rows[row_index][column_index]

    def setValue(self, row_index, column_index, value):
        self._rows[row_index][column_index] = value

    def copy(self):
        table = Table()
        for column in self._columns: # todo: copy visual properties
            table.new_column(column.identifier)
        for row in self._rows:
            new_row = table.new_row()
            new_row._values = row._values[:]
        return table


class TableModel(QtCore.QAbstractTableModel):
    def __init__(self, table):
        super().__init__(None) # no parent
        assert isinstance(table, Table)
        self.table = table

    def rowCount(self, parent):
        return self.table.row_count()

    def columnCount(self, parent):
        return self.table.column_count()

    def data(self, index, role):
        if index.isValid():
            value = self.table.getValue(index.row(), index.column())
            return self.table.column(index.column()).row_item.data(role, value)

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        # editable model - data may be edited through an item delegate editor
        # (DateEdit, DecimalEdit, QLineEdit, etc.)
        if index.isValid():
            if role == QtCore.Qt.CheckStateRole:
                value = value == QtCore.Qt.Checked
                role = QtCore.Qt.EditRole  # reuse the code
            if role == QtCore.Qt.EditRole:
                row = self.table.row(index.row())
                row[index.column()] = value
                self.dataChanged.emit(index, index)
                column = self.table.column(index.column())
                if column.on_edited:
                    try:
                        column.on_edited(row, column, value)
                    except Exception as exc:
                        print(exc)
                return True
        return False

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self.table.column(section).label
            else:
                return self.table.column(section).header_item.data(role, None)
        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return str(section)  # for rows display row number
        return None

    def flags(self, index):
        if index.isValid():
            return self.table.column(index.column()).row_item.flags
        return QtCore.Qt.ItemIsEnabled

    def eventFilter(self, table_view, event):  # target - tableView
        """Hook pressing Enter to start editing a table item.
        """
        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if event.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
                if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    if table_view.state() != table_view.EditingState:
                        index = table_view.currentIndex()
                        if table_view.model().flags(index) & QtCore.Qt.ItemIsEditable:
                            table_view.edit(index)
                            return True
        return super().eventFilter(table_view, event) # standard event processing


def test():
    app = QtWidgets.QApplication([])

    tableView = QtWidgets.QTableView(None)

    table = Table(tableView)
    table.new_column('column1', label='int', default=0, width=50)
    table.new_column('column2', label='Decimal', editable=True, alignment=QtCore.Qt.AlignRight,
                     default=Decimal())
    table.new_column('column3', label='Date', editable=True, default=Date())
    for rowIndex in range(10):
        row = table.new_row()
        row.column1 = rowIndex + 1
        row.column2 = Decimal(rowIndex)

    tableView.show()
    app.exec()


if __name__ == '__main__':
    test()
