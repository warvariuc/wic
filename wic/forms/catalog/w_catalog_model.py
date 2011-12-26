"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.datetime import Date, _format as formatDate
import traceback

import orm


from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit



class WItemStyle():
    """Common style for representation of an ItemView item"""

    def __init__(self, roles={}, **kwargs):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                      QtCore.Qt.DisplayRole: self.displayRole
        }
        _roles.update(roles)
        self.roles = _roles
        self.__dict__.update(kwargs)


    def data(self, role, value=None): # http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
        data = self.roles.get(role)
        return data(value) if hasattr(data, '__call__') else data

    def displayRole(self, value):
        return str(value) if value else ''


class WDecimalItemStyle(WItemStyle):
    """Style for items with Decimal values."""

    def __init__(self, roles={}, format=''):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight,
                      QtCore.Qt.DisplayRole: self.displayRole}
        _roles.update(roles)
        super().__init__(roles=_roles, format=format)

    def displayRole(self, value):
        format_ = self.format
        if format_:
            if format_[-1:] == ' ':
                if not value:
                    return ''
                format_ = format_[:-1]
            return format(value, format_)


class WDateItemStyle(WItemStyle):
    """Style for items with Date values."""

    def __init__(self, roles={}):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter,
                  QtCore.Qt.DisplayRole: formatDate}
        _roles.update(roles)
        super().__init__(roles=_roles)


class WBoolItemStyle(WItemStyle):
    """Style for items with bool values."""

    def __init__(self, roles={}):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter,
                  QtCore.Qt.DisplayRole: None,
                  QtCore.Qt.CheckStateRole: lambda value: QtCore.Qt.Checked if value else QtCore.Qt.Unchecked}
        _roles.update(roles)
        super().__init__(roles=_roles)


class WVHeaderStyle(WItemStyle):
    """Style for vertical headers."""

    def __init__(self, roles={}, title='', width=None):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                  QtCore.Qt.DisplayRole: title}
        _roles.update(roles)
        super().__init__(roles=_roles, title=title, width=width)

    def displayRole(self, value):
        format_ = self.format
        if format_:
            if format_[-1:] == ' ':
                if not value:
                    return ''
                format_ = format_[:-1]
            return format(value, format_)

class WHHeaderStyle(WItemStyle):
    """Style for horizontal headers."""

    def __init__(self, roles={}, height=None):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                  QtCore.Qt.DisplayRole: lambda value: value}
        _roles.update(roles)
        super().__init__(roles=_roles, height=height)

    def displayRole(self, value):
        format_ = self.format
        if format_:
            if format_[-1:] == ' ':
                if not value:
                    return ''
                format_ = format_[:-1]
            return format(value, format_)


def createStyleForField(field):
    assert isinstance(field, orm.Field)
    if isinstance(field, orm.DecimalField):
        return WDecimalItemStyle(format=',.%if ' % field.fractionDigits)
    elif isinstance(field, orm.DateField):
        return WDateItemStyle()
    elif isinstance(field, orm.BooleanField):
        return WBoolItemStyle()
    else:
        return WItemStyle()




class WCatalogProxyModel(QtCore.QAbstractTableModel):
    """Model for showing list of catalog items."""

    def __init__(self, db, catalogModel, where=None):
        assert orm.isModel(catalogModel)
        super().__init__(None) # no parent
        self._hHeaderStyle = WHHeaderStyle()
        fields = []
        self._vHeaderStyles = []
        self._columnStyles = []
        for field in catalogModel:
            fields.append(field)
            self._vHeaderStyles.append(WVHeaderStyle(title=field.label))
            self._columnStyles.append(createStyleForField(field))

        self.db = db
        self.catalogModel = catalogModel
        self.fields = fields
        self.where = where
        self.updateTime = 5000 # milliseconds
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.refresh)
        self._rowsCount = None
        self.rows = None
        
        orm.signals.post_save.connect(self.refresh, catalogModel)
        orm.signals.post_delete.connect(self.refresh, catalogModel)


    def item(self, rowNo, columnNo):
        ""
        if self.rows is None:
            self.refresh()
        return self.rows[rowNo][columnNo]

    def refresh(self, **kwargs):
        #print('Refresh')
        self.timer.stop()
        self.beginResetModel()
        self._rowsCount = None
        self.rows = self.db.select(*self.fields, where=self.where)
        self.endResetModel()

        self.timer.start(self.updateTime)

    def getRowId(self, rowNo):
        """"""
        return self.rows.value(rowNo, self.catalogModel.id)

    def rowCount(self, parent):
        if self._rowsCount is None:
            self._rowsCount = self.catalogModel.count(self.db)
        return self._rowsCount

    def columnCount(self, parent):
        return len(self._columnStyles)

    def data(self, index, role):
        if index.isValid():
            value = self.item(index.row(), index.column())
            return self._columnStyles[index.column()].data(role, value)

#    def flags(self, index):
#        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            return self._vHeaderStyles[section].data(role)
        elif orientation == QtCore.Qt.Vertical:
            return self._hHeaderStyle.data(role, section)
        return None


#    def setQuery(self, model, fields, where):
#        """"""
#        assert isinstance(model, orm.Model), 'Pass an orm.Model instance'
#        assert all(isinstance(field, orm.Field) for field in fields), 'All fields must be instances of orm.Field'





#if __name__ == '__main__': # some tests
#    app = QtGui.QApplication([])
#
#    tableView = QtGui.QTableView(None)
#
#    table = WTable(tableView)
#    table.newColumn('column1', label = 'int', default = 0, width = 50)
#    table.newColumn('column2', label = 'Decimal', editable = True, alignment = QtCore.Qt.AlignRight, default = Dec())
#    table.newColumn('column3', label = 'Date', editable = True, default = Date())
#    for rowIndex in range(10):
#        row = table.newRow()
#        row.column1 = rowIndex + 1
#        row.column2 = Dec(rowIndex)
#
#    tableView.show()
#    app.exec()
