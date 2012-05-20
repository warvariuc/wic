__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.datetime import Date, _format as formatDate
import traceback, time, inspect

import orm, wic



class Role():
    """
    """
    def __init__(self, QtRole, value = None):
        assert isinstance(QtRole, int)
        self.QtRole = QtRole
        self.value = value

    def __call__(self, func):
        self.value = func
        return self



class WStyle():
    """Common style for representation of an ItemView item
    http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.data = self.getRoles()
#        print(self.data)

    @Role(QtCore.Qt.DisplayRole)
    def display(self, value): # data to be rendered in the form of text
        return value
        #return None if value is None else str(value)

    @Role(QtCore.Qt.ToolTipRole)
    def toolTip(self, value):
        return value
        #return None if value is None else str(value)

    textAlignment = Role(QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
    decoration = Role(QtCore.Qt.DecorationRole, None)
    checkState = Role(QtCore.Qt.CheckStateRole, None)
    sizeHint = Role(QtCore.Qt.SizeHintRole, None)

    def getRoles(self):
        roles = {}
        for attrName, attrValue in inspect.getmembers(self):
            if isinstance(attrValue, Role):
                assert attrValue.QtRole not in roles, 'The same role is met twice with different names.'
                roles[attrValue.QtRole] = attrValue.value
        return roles


class WDecimalStyle(WStyle):
    """Style for items with Decimal values.
    """
    @Role(QtCore.Qt.DisplayRole)
    def display(self, value):
        format_ = self.format
        if format_:
            if format_.endswith(' '):
                if not value:
                    return ''
                format_ = format_[:-1]
            return format(value, format_)

    textAlignment = Role(QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)


class WDateStyle(WStyle):
    """Style for items with Date values.
    """
    display = Role(QtCore.Qt.DisplayRole, formatDate)
    textAlignment = Role(QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)


class WBoolStyle(WStyle):
    """Style for items with bool values.
    """
    @Role(QtCore.Qt.CheckStateRole)
    def checkState(self, value, checked = QtCore.Qt.Checked, unchecked = QtCore.Qt.Unchecked): # attr lookup optimization
        return checked if value else unchecked
    textAlignment = Role(QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
    display = Role(QtCore.Qt.DisplayRole, None)


class WRecordStyle(WStyle):
    """Style for items which contains record ids.
    """
    @Role(QtCore.Qt.DisplayRole)
    def display(self, record):
        return None if record is None else str(record)



class WHHeaderStyle(WStyle):
    """Style for horizontal headers.
    """
    def __init__(self, *args, title, width = 0, **kwargs):
        self.display = Role(QtCore.Qt.DisplayRole, title) # title is constant - override display
        #self.sizeHint = Role(QtCore.Qt.SizeHintRole, QtCore.QSize(width, 0))
        super().__init__(*args, **kwargs)


class WVHeaderStyle(WStyle):
    """Style for vertical headers.
    """
    def __init__(self, *args, height = 0, **kwargs):
        #self.sizeHint = Role(QtCore.Qt.SizeHintRole, QtCore.QSize(0, height))
        super().__init__(*args, **kwargs)






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
        self._vHeaderStyle = WVHeaderStyle() # one style for all rows
        self._hHeaderStyles = []
        self._columnStyles = []
        for field in catalogModel:
            self._hHeaderStyles.append(WHHeaderStyle(title = field.label))
            columnStyle = self._createStyleForField(field)
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
            return WDecimalStyle(format = ',.%if ' % field.fractionDigits, fieldName = field.name)
        elif isinstance(field, orm.DateField):
            return WDateStyle(fieldName = field.name)
        elif isinstance(field, orm.BooleanField):
            return WBoolStyle(fieldName = field.name)
        elif isinstance(field, orm.RecordField):
            return WRecordStyle(fieldName = field.name)
        else:
            return WStyle(fieldName = field.name)

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
            style = self._columnStyles[index.column()]
            data = style.data.get(role)

            if not hasattr(data, '__call__'): # not a function to call
                return data

            item = self.item(index.row())
            value = getattr(item, style.fieldName)

            return data(style, value) # call the function

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
            style = self._hHeaderStyles[section]
        elif orientation == QtCore.Qt.Vertical:
            style = self._vHeaderStyle
        else:
            return None
        data = style.data.get(role)
        return data(style, section) if hasattr(data, '__call__') else data
