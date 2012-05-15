__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.datetime import Date, _format as formatDate
import traceback, time

import orm, wic


class WStyle():
    """Common style for representation of an ItemView item
    """
    def __init__(self, roles = {}, **kwargs):
        assert isinstance(roles, dict), 'Roles should a dict {role: value|function}'
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                  QtCore.Qt.DisplayRole: self.displayRole, QtCore.Qt.ToolTipRole: self.toolTipRole
        }
        _roles.update(roles)
        self.roles = _roles
        self.__dict__.update(kwargs)

    def data(self, role, value = None):
        """Process value from the db and return data for the given role.
        @param role: data role (http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum)
        @param value: value from the db to analyze or process
        """
        data = self.roles.get(role)
        return data(value) if callable(data) else data

    def displayRole(self, value):
        return str(value) if value else ''

    def toolTipRole(self, value):
        return str(value) if value else None


class WDecimalStyle(WStyle):
    """Style for items with Decimal values.
    """
    def __init__(self, roles = {}, format = ''):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight,
                      QtCore.Qt.DisplayRole: self.displayRole}
        _roles.update(roles)
        super().__init__(roles = _roles, format = format)

    def displayRole(self, value):
        format_ = self.format
        if format_:
            if format_[-1:] == ' ':
                if not value:
                    return ''
                format_ = format_[:-1]
            return format(value, format_)


class WDateStyle(WStyle):
    """Style for items with Date values.
    """
    def __init__(self, roles = {}):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter,
                  QtCore.Qt.DisplayRole: formatDate}
        _roles.update(roles)
        super().__init__(roles = _roles)


class WBoolStyle(WStyle):
    """Style for items with bool values.
    """
    def __init__(self, roles = {}):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter,
                  QtCore.Qt.DisplayRole: None,
                  QtCore.Qt.CheckStateRole: lambda value: QtCore.Qt.Checked if value else QtCore.Qt.Unchecked}
        _roles.update(roles)
        super().__init__(roles = _roles)


class WRecordStyle(WStyle):
    """Style for items which contains record ids.
    """
    def __init__(self, roles = {}):
        _roles = {QtCore.Qt.DisplayRole: self.displayRole}
        _roles.update(roles)
        super().__init__(roles = _roles, format = format)

    def displayRole(self, record):
        return '' if record is None else str(record)


class WHHeaderStyle(WStyle):
    """Style for horizontal headers.
    """
    def __init__(self, roles = {}, title = '', width = None):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                  QtCore.Qt.DisplayRole: title}
        _roles.update(roles)
        super().__init__(roles = _roles, title = title, width = width)

    def displayRole(self, value):
        format_ = self.format
        if format_:
            if format_[-1:] == ' ':
                if not value:
                    return ''
                format_ = format_[:-1]
            return format(value, format_)

class WVHeaderStyle(WStyle):
    """Style for vertical headers.
    """
    def __init__(self, roles = {}, height = None):
        _roles = {QtCore.Qt.TextAlignmentRole: QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft,
                  QtCore.Qt.DisplayRole: lambda value: value}
        _roles.update(roles)
        super().__init__(roles = _roles, height = height)

    def displayRole(self, value):
        format_ = self.format
        if format_:
            if format_[-1:] == ' ':
                if not value:
                    return ''
                format_ = format_[:-1]
            return format(value, format_)




class CatalogModel(orm.Model):
    """Base model for all catalogs.
    """
    deleted = orm.BooleanField()

    @classmethod
    def _handleTableMissing(cls, db):
        """Default implementation of situation when upon checking there was not found the table 
        corresponding to this model in the db.
        """
        if QtGui.QMessageBox.question(wic.app.mainWindow, 'Automatically create table?',
                'Table `%s` which corresponds to model `%s.%s` does not exist in the database `%s`.\n\n'
                'Do you want it to be automatically created?'
                % (cls, cls.__module__, cls.__name__, db.uri), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
            db.execute(db.getCreateTableQuery(cls))
            QtGui.QMessageBox.information(wic.app.mainWindow, 'Done', 'The table was successfully created.')
        else:
            super()._handleTableMissing(db)



class WCatalogViewModel(QtCore.QAbstractTableModel):
    """Qt table model for showing list of catalog items.
    """
    def __init__(self, db, catalogModel, where = None):
        assert isinstance(catalogModel, type) and issubclass(catalogModel, CatalogModel), 'Pass a CatalogModel subclass'
        super().__init__(None) # no parent
        self._vHeaderStyle = WVHeaderStyle()
        self._hHeaderStyles = []
        self._columnStyles = []
        for field in catalogModel:
            self._hHeaderStyles.append(WHHeaderStyle(title = field.label))
            columnStyle = self._createStyleForField(field)
            columnStyle.fieldName = field.name
            self._columnStyles.append(columnStyle)

        self._columnCount = len(self._columnStyles)
        self._db = db
        self._catalogModel = catalogModel
        self._where = where

        self._updatePeriod = 5 # seconds
        self._fetchCount = 150 # number of records to fetch in one db request
        self._updateTimer = QtCore.QTimer(self) # timer for updating the view
        self._updateTimer.setSingleShot(True)
        self._updateTimer.timeout.connect(self._resetCache)
        orm.signals.post_save.connect(self._resetCache, catalogModel) # to update the view...
        orm.signals.post_delete.connect(self._resetCache, catalogModel) # ...when a record was modified
        self._resetCache()

    def _createStyleForField(self, field):
        assert isinstance(field, orm.Field)
        if isinstance(field, orm.DecimalField):
            return WDecimalStyle(format = ',.%if ' % field.fractionDigits)
        elif isinstance(field, orm.DateField):
            return WDateStyle()
        elif isinstance(field, orm.BooleanField):
            return WBoolStyle()
        elif isinstance(field, orm.RecordField):
            return WRecordStyle()
        else:
            return WStyle()

    def _resetCache(self, **kwargs):
        #print('clearCache')
        self._updateTimer.stop()
        self.beginResetModel()
        self._cache = {}  # {rowNo: (catalogItem, fetch_time)}
        self._rowCount = None
        self.endResetModel()
        self._updateTimer.start(self._updatePeriod * 1000)

    def item(self, rowNo):
        """Get an item from the cache. If it's not in the cache, fetch a range from DB and update the cache.
        @param rowNo: row number from the view for which to get the item
        """
        try: # find the row in the cache
            return self._cache[rowNo][0]
        except KeyError: # fill the cache
            #print('Trying to retrieve row %d', rowNo)
            self._updateTimer.stop()
            rangeStart = max(rowNo - self._fetchCount // 3, 0)
            items = self._catalogModel.get(self._db, where = self._where, limit = (rangeStart, self._fetchCount), select_related = True)
            now = time.time()
            expiredTime = now - self._updatePeriod
            cache = self._cache
            # clean the cache of expired rows
            for rowNo in tuple(cache.keys()):
                if cache[rowNo][1] <= expiredTime:
                    cache.pop(rowNo)
            #print('for rowNo, item in enumerate(items, rangeStart):')
            for rowNo, item in enumerate(items, rangeStart):
                #print(rowNo, item)
                cache[rowNo] = (item, now)
            self._updateTimer.start(self._updatePeriod * 1000)
            return cache[rowNo][0]

    def data(self, index, role):
        if index.isValid():
            item = self.item(index.row())
            columnStyle = self._columnStyles[index.column()]
            value = getattr(item, columnStyle.fieldName)
            return columnStyle.data(role, value)

    def rowCount(self, parent):
        _rowCount = self._rowCount # cached row count
        if _rowCount is None: # if it's not filled yet - fetch it from the db
            _rowCount = self._rowCount = self._catalogModel.getCount(self._db, where = self._where)
            #print('rowCount', _rowsCount)
        return _rowCount

    def columnCount(self, parent):
        return self._columnCount

#    def flags(self, index):
#        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            return self._hHeaderStyles[section].data(role)
        elif orientation == QtCore.Qt.Vertical:
            return self._vHeaderStyle.data(role, section)
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
