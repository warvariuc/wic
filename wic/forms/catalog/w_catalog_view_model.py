__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.datetime import Date, _format as formatDate
import traceback, time, inspect, sys

import orm, wic



class Role():
    """
    """
    def __init__(self, QtRole, value = None):
        """
        @param QtRole: http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
        """
        assert isinstance(QtRole, int)
        self.QtRole = QtRole
        self.value = value

    def __call__(self, func):
        self.value = func
        return self


DefaultSectionSizeRole = QtCore.Qt.UserRole

class Styles:

    class Style():
        """Common style for representation of an ItemView item
        """
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.getRoles()
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
            """Walk over all role attributes of this style and put them in `data` attribute as dictionary {QtStyle: value}.
            """
            roles = {}
            for attr_name, attrValue in inspect.getmembers(self):
                if isinstance(attrValue, Role):
                    assert attrValue.QtRole not in roles, 'The same role is met twice with different names.'
                    roles[attrValue.QtRole] = attrValue.value
            self.data = roles
    
    
    class DecimalStyle(Style):
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
    
    
    class DateStyle(Style):
        """Style for items with Date values.
        """
        display = Role(QtCore.Qt.DisplayRole, formatDate)
        textAlignment = Role(QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
    
    
    class BoolStyle(Style):
        """Style for items with bool values.
        """
        @Role(QtCore.Qt.CheckStateRole)
        def checkState(self, value, checked = QtCore.Qt.Checked, unchecked = QtCore.Qt.Unchecked): # attr lookup optimization
            return checked if value else unchecked
    
        textAlignment = Role(QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        display = Role(QtCore.Qt.DisplayRole, None)
    
    
    class RecordStyle(Style):
        """Style for items which contains record ids.
        """
        @Role(QtCore.Qt.DisplayRole)
        def display(self, record):
            return None if record is None else str(record)
    
    
    
    class HHeaderStyle(Style):
        """Style for a horizontal header.
        """
        def __init__(self, *args, field, **kwargs):
            self.display = Role(QtCore.Qt.DisplayRole, field.label) # title is constant - override display
            super().__init__(*args, **kwargs)
    
    
    class VHeaderStyle(Style):
        """Style for a vertical header.
        """
        def __init__(self, *args, **kwargs):
            rowHeight = QtGui.QFontMetrics(QtGui.QApplication.font()).height() + 4 # font height and some spare pixels
            self.defaultSectionSize = Role(DefaultSectionSizeRole, rowHeight)
            super().__init__(*args, **kwargs)


    @classmethod
    def createStyleForField(cls, field):
        assert isinstance(field, orm.ModelField)

        if isinstance(field, orm.DecimalField):
            return cls.DecimalStyle(format = ',.%if ' % field.fractionDigits, fieldName = field.name)
        elif isinstance(field, orm.DateField):
            return cls.DateStyle(fieldName = field.name)
        elif isinstance(field, orm.BooleanField):
            return cls.BoolStyle(fieldName = field.name)
        elif isinstance(field, orm.RelatedRecordField):
            return cls.RecordStyle(fieldName = field.name)
        else:
            return cls.Style(fieldName = field.name)





class CatalogModel(orm.Model):
    """Base model for all catalogs.
    """
    deleted = orm.BooleanField()

    @classmethod
    def _handle_table_missing(cls, db):
        """Default implementation of situation when upon checking there was not found the table 
        corresponding to this model in the db.
        """
        if QtGui.QMessageBox.question(wic.app.mainWindow, 'Automatically create table?',
                'Table `%s` which corresponds to model `%s.%s` does not exist in the database `%s`.\n\n'
                'Do you want it to be automatically created?'
                % (cls, cls.__module__, cls.__name__, db.uri), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
            db.execute(db.get_create_table_query(cls))
            QtGui.QMessageBox.information(wic.app.mainWindow, 'Done', 'The table was successfully created.')
        else:
            super()._handle_table_missing(db)



class WCatalogViewModel(QtCore.QAbstractTableModel):
    """Qt table model for showing list of catalog items.
    """
    _styles = Styles
    
    def __init__(self, db, catalogModel, where = None):
        assert isinstance(catalogModel, type) and issubclass(catalogModel, CatalogModel), 'Pass a CatalogModel subclass'
        super().__init__(None) # no parent
        self.vHeaderStyle = self._styles.VHeaderStyle() # one style for all rows
        self.hHeaderStyles = []
        self.columnStyles = []
        for field in catalogModel._meta.fields.values():
            self.hHeaderStyles.append(self._styles.HHeaderStyle(field = field))
            columnStyle = self._styles.createStyleForField(field)
            self.columnStyles.append(columnStyle)

        self._columnCount = len(self.columnStyles)
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
            items = self._catalogModel.objects.get(self._db, where = self._where, limit = (rangeStart, self._fetchCount), select_related = True)
            now = time.time()
            expiredTime = now - self._updatePeriod
            cache = self._cache
            # clean the cache of expired rows
            for _rowNo in tuple(cache.keys()):
                if cache[_rowNo][1] <= expiredTime:
                    cache.pop(_rowNo)
            #print('for rowNo, item in enumerate(items, rangeStart):')
            for _rowNo, item in enumerate(items, rangeStart):
                cache[_rowNo] = (item, now)
            self._updateTimer.start(self._updatePeriod * 1000)
            return cache[rowNo][0]

    def data(self, index, role):
        if index.isValid():
            style = self.columnStyles[index.column()]
            data = style.data.get(role)

            if not hasattr(data, '__call__'): # not a function to call
                return data

            item = self.item(index.row())
            value = getattr(item, style.fieldName)

            return data(style, value) # call the function

    def rowCount(self, parent):
        _rowCount = self._rowCount # cached row count
        if _rowCount is None: # if it's not filled yet - fetch it from the db
            _rowCount = self._rowCount = self._catalogModel.objects.get_count(self._db,
                                                                              where = self._where)
            #print('rowCount', _rowsCount)
        return _rowCount

    def columnCount(self, parent):
        return self._columnCount

#    def flags(self, index):
#        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            style = self.hHeaderStyles[section]
        elif orientation == QtCore.Qt.Vertical:
            style = self.vHeaderStyle
        else:
            return None
        data = style.data.get(role)
        return data(style, section) if hasattr(data, '__call__') else data
