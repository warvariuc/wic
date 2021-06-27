from PyQt5 import QtGui, QtCore, QtWidgets
from wic.datetime import format as format_date
import time, inspect

import peewee
import wic


class Role():
    """
    """
    def __init__(self, role, value = None):
        """

        Args:
            role: http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
        """
        assert isinstance(role, int)
        self.role = role
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
            self.get_roles()
    #        print(self.data)

        @Role(QtCore.Qt.DisplayRole)
        def display(self, value):  # data to be rendered in the form of text
            return value
            #return None if value is None else str(value)

        @Role(QtCore.Qt.ToolTipRole)
        def toolTip(self, value):
            return value
            #return None if value is None else str(value)
    
        text_alignment = Role(
            QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        decoration = Role(QtCore.Qt.DecorationRole, None)
        check_state = Role(QtCore.Qt.CheckStateRole, None)
        size_hint = Role(QtCore.Qt.SizeHintRole, None)
    
        def get_roles(self):
            """Walk over all role attributes of this style and put them in `data` attribute as dictionary {QtStyle: value}.
            """
            roles = {}
            for attr_name, attr_value in inspect.getmembers(self):
                if isinstance(attr_value, Role):
                    assert attr_value.role not in roles, \
                        'The same role is met twice with different names.'
                    roles[attr_value.role] = attr_value.value
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
    
        text_alignment = Role(
            QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

    class DateStyle(Style):
        """Style for items with Date values.
        """
        display = Role(QtCore.Qt.DisplayRole, format_date)
        text_alignment = Role(
            QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)

    class BoolStyle(Style):
        """Style for items with bool values.
        """
        @Role(QtCore.Qt.CheckStateRole)
        # attr lookup optimization
        def check_state(self, value, checked=QtCore.Qt.Checked, unchecked=QtCore.Qt.Unchecked):
            return checked if value else unchecked
    
        text_alignment = Role(
            QtCore.Qt.TextAlignmentRole, QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
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
            # title is constant - override display
            self.display = Role(QtCore.Qt.DisplayRole, field.verbose_name or field.name)
            super().__init__(*args, **kwargs)

    class VHeaderStyle(Style):
        """Style for a vertical header.
        """
        def __init__(self, *args, **kwargs):
            # font height and some spare pixels
            row_height = QtGui.QFontMetrics(QtWidgets.QApplication.font()).height() + 4
            self.defaultSectionSize = Role(DefaultSectionSizeRole, row_height)
            super().__init__(*args, **kwargs)

    @classmethod
    def create_style_for_field(cls, field):
        assert isinstance(field, peewee.Field)

        if isinstance(field, peewee.DecimalField):
            return cls.DecimalStyle(format=f',.%{field.decimal_places}f', field_name=field.name)
        elif isinstance(field, peewee.DateField):
            return cls.DateStyle(field_name=field.name)
        elif isinstance(field, peewee.BooleanField):
            return cls.BoolStyle(field_name=field.name)
        elif isinstance(field, peewee.ForeignKeyField):
            return cls.RecordStyle(field_name=field.name)
        return cls.Style(field_name=field.name)


class CatalogModel(peewee.Model):
    """Base model for all catalogs.
    """
    deleted = peewee.BooleanField()

    class Meta:
        database = wic.database_proxy  # Use proxy for our DB.

    # @classmethod
    # def _handleTableMissing(cls, db):
    #     """Default implementation of situation when upon checking there was not found the table
    #     corresponding to this model in the db.
    #     """
    #     if QtWidgets.QMessageBox.question(
    #             wic.app.mainWindow, 'Automatically create table?',
    #             'Table `%s` which corresponds to model `%s.%s` does not exist in the database '
    #             '`%s`.\n\nDo you want it to be automatically created?'
    #             % (cls, cls.__module__, cls.__name__, db.uri),
    #             QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
    #             QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes:
    #         db.execute(db.getCreateTableQuery(cls))
    #         QtWidgets.QMessageBox.information(
    #             wic.app.mainWindow, 'Done', 'The table was successfully created.')
    #     else:
    #         super()._handleTableMissing(db)


class CatalogViewModel(QtCore.QAbstractTableModel):
    """Qt table model for showing list of catalog items.
    """
    _styles = Styles
    
    def __init__(self, catalog_model, where=None):
        assert isinstance(catalog_model, type) and issubclass(catalog_model, CatalogModel), \
            'Pass a CatalogModel subclass'
        super().__init__(None)  # no parent
        self.vHeaderStyle = self._styles.VHeaderStyle()  # one style for all rows
        self.hHeaderStyles = []
        self.column_styles = []
        for field in catalog_model._meta.sorted_fields:
            self.hHeaderStyles.append(self._styles.HHeaderStyle(field=field))
            column_style = self._styles.create_style_for_field(field)
            self.column_styles.append(column_style)

        self._column_count = len(self.column_styles)
        self._catalog_model = catalog_model
        self._where = where

        self._update_period = 5  # seconds
        self._fetch_count = 150  # number of records to fetch in one db request
        self._update_timer = QtCore.QTimer(self)  # timer for updating the view
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._reset_cache)
        # orm.signals.post_save.connect(self._resetCache, catalog_model)  # to update the view...
        # orm.signals.post_delete.connect(self._resetCache, catalog_model)  # ...when a record was modified
        self._reset_cache()

    def _reset_cache(self, **kwargs):
        #print('clearCache')
        self._update_timer.stop()
        self.beginResetModel()
        self._cache = {}  # {rowNo: (catalogItem, fetch_time)}
        self._row_count = None
        self.endResetModel()
        self._update_timer.start(self._update_period * 1000)

    def item(self, row_no):
        """Get an item from the cache. If it's not in the cache, fetch a range from DB and update the cache.

        Args:
            row_no: row number from the view for which to get the item
        """
        try:  # find the row in the cache
            return self._cache[row_no][0]
        except KeyError:  # fill the cache
            pass
        # print('Trying to retrieve row %d', rowNo)
        self._update_timer.stop()
        range_start = max(row_no - self._fetch_count // 3, 0)
        items = self._catalog_model.select().where(
            self._where).offset(range_start).limit(self._fetch_count)

        now = time.time()
        expired_time = now - self._update_period
        cache = self._cache
        # clean the cache of expired rows
        for _rowNo in tuple(cache.keys()):
            if cache[_rowNo][1] <= expired_time:
                cache.pop(_rowNo)
        # print('for rowNo, item in enumerate(items, rangeStart):')
        for _rowNo, item in enumerate(items, range_start):
            cache[_rowNo] = (item, now)
        self._update_timer.start(self._update_period * 1000)
        return cache[row_no][0]

    def data(self, index, role):
        if index.isValid():
            style = self.column_styles[index.column()]
            data = style.data.get(role)

            if not hasattr(data, '__call__'): # not a function to call
                return data

            item = self.item(index.row())
            value = getattr(item, style.field_name)

            return data(style, value) # call the function

    def rowCount(self, parent):
        _row_count = self._row_count  # cached row count
        if _row_count is None:  # if it's not filled yet - fetch it from the db
            _row_count = self._row_count = self._catalog_model.select().where(self._where).count()
        return _row_count

    def columnCount(self, parent):
        return self._column_count

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
