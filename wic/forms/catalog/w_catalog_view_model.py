__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from PyQt4 import QtGui, QtCore
from decimal import Decimal as Dec
from wic.datetime import Date, _format as formatDate
import traceback, time, inspect, sys

import orm, wic



class Role():
    """
    """
    def __init__(self, qt_role, value=None):
        """
        @param qt_role: http://doc.qt.nokia.com/stable/qt.html#ItemDataRole-enum
        """
        assert isinstance(qt_role, int)
        self.qt_role = qt_role
        self.value = value

    def __call__(self, func):
        self.value = func
        return self


default_section_size_role = QtCore.Qt.UserRole


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

        text_alignment = Role(QtCore.Qt.TextAlignmentRole,
                              QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
        decoration = Role(QtCore.Qt.DecorationRole, None)
        check_state = Role(QtCore.Qt.CheckStateRole, None)
        size_hint = Role(QtCore.Qt.SizeHintRole, None)

        def get_roles(self):
            """Walk over all role attributes of this style and put them in `data` attribute as
            dictionary {QtStyle: value}.
            """
            roles = {}
            for attr_name, attr_value in inspect.getmembers(self):
                if isinstance(attr_value, Role):
                    assert attr_value.qt_role not in roles, \
                        'The same role is met twice with different names.'
                    roles[attr_value.qt_role] = attr_value.value
            self.data = roles


    class RecordIdStyle(Style):
        """Style for items with record ids.
        """
        text_alignment = Role(QtCore.Qt.TextAlignmentRole,
                              QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)


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

        text_alignment = Role(QtCore.Qt.TextAlignmentRole,
                              QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)


    class DateStyle(Style):
        """Style for items with Date values.
        """
        display = Role(QtCore.Qt.DisplayRole, formatDate)
        text_alignment = Role(QtCore.Qt.TextAlignmentRole,
                              QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)


    class BoolStyle(Style):
        """Style for items with bool values.
        """
        @Role(QtCore.Qt.CheckStateRole)
        def check_state(self, value, checked=QtCore.Qt.Checked, unchecked=QtCore.Qt.Unchecked):  # attr lookup optimization
            return checked if value else unchecked

        text_alignment = Role(QtCore.Qt.TextAlignmentRole,
                              QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        display = Role(QtCore.Qt.DisplayRole, None)


    class RelatedRecordStyle(Style):
        """Style for items which contains record ids.
        """
        @Role(QtCore.Qt.DisplayRole)
        def display(self, record):
            return None if record is None else str(record)


    class HorizontalHeaderStyle(Style):
        """Style for a horizontal header.
        """
        def __init__(self, *args, field, **kwargs):
            self.display = Role(QtCore.Qt.DisplayRole, field.label)  # title is constant - override display
            super().__init__(*args, **kwargs)


    class VerticalHeaderStyle(Style):
        """Style for a vertical header.
        """
        def __init__(self, *args, **kwargs):
            row_height = QtGui.QFontMetrics(QtGui.QApplication.font()).height() + 4  # font height and some spare pixels
            self.default_section_size = Role(default_section_size_role, row_height)
            super().__init__(*args, **kwargs)


    @classmethod
    def create_style_for_field(cls, field):
        assert isinstance(field, orm.ModelField)

        if isinstance(field, orm.IdField):
            return cls.RecordIdStyle(field_name=field.name)
        elif isinstance(field, orm.DecimalField):
            return cls.DecimalStyle(format=',.%if ' % field.decimal_places, field_name=field.name)
        elif isinstance(field, orm.DateField):
            return cls.DateStyle(field_name=field.name)
        elif isinstance(field, orm.BooleanField):
            return cls.BoolStyle(field_name=field.name)
        elif isinstance(field, orm.RelatedRecordField):
            return cls.RelatedRecordStyle(field_name=field.name)
        else:
            return cls.Style(field_name=field.name)





class CatalogModel(orm.Model):
    """Base model for all catalogs.
    """
    deleted = orm.BooleanField(comment='Whether the record is marked as deleted.')

    @classmethod
    def _handle_table_missing(cls, db):
        """Default implementation of situation when upon checking there was not found the table 
        corresponding to this model in the db.
        """
        if QtGui.QMessageBox.question(wic.app.mainWindow, 'Automatically create table?',
                'Table `%s` which corresponds to model `%s.%s` does not exist in the database `%s`.\n\n'
                'Do you want it to be automatically created?'
                % (cls, cls.__module__, cls.__name__, db.uri),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
            for query in db.get_create_table_query(cls):
                db.execute(query)
            wic.app.mainWindow.showInformation('Done', 'The table was successfully created.')
        else:
            super()._handle_table_missing(db)



class WCatalogViewModel(QtCore.QAbstractTableModel):
    """Qt table model for showing list of catalog items.
    """
    _styles = Styles

    def __init__(self, db, catalog_model, where=None):
        assert isinstance(catalog_model, type) and issubclass(catalog_model, CatalogModel), \
            'Pass a CatalogModel subclass'
        super().__init__(None)  # no parent
        self.v_header_style = self._styles.VerticalHeaderStyle()  # one style for all rows
        self.h_header_styles = []
        self.column_styles = []
        for field in catalog_model._meta.fields.values():
            self.h_header_styles.append(self._styles.HorizontalHeaderStyle(field=field))
            column_style = self._styles.create_style_for_field(field)
            self.column_styles.append(column_style)

        self._column_count = len(self.column_styles)
        self._db = db
        self._catalog_model = catalog_model
        self._where = where

        self._update_interval = 5  # seconds
        self._fetch_count = 150  # number of records to fetch in one db query
        self._refresh_timer = QtCore.QTimer(self)  # timer for updating the view
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._reset_cache)
        orm.signals.post_save.connect(self._reset_cache, catalog_model)  # to update the view...
        orm.signals.post_delete.connect(self._reset_cache, catalog_model)  # ...when a record was modified
        self._reset_cache()

    def _reset_cache(self, **kwargs):
        #print('clearCache')
        self._refresh_timer.stop()
        self.beginResetModel()
        self._cache = {}  # {row_no: (catalogItem, fetch_time)}
        self._row_count = None
        self.endResetModel()
        self._refresh_timer.start(self._update_interval * 1000)

    def item(self, row_no):
        """Get an item from the cache. If it's not in the cache, fetch a range from DB and update
            the cache.
        @param row_no: row number from the view for which to get the item
        """
        try:
            # find the row in the cache
            return self._cache[row_no][0]
        except KeyError:
            pass
        # fill the cache
        #print('Trying to retrieve row %d', row_no)
        self._refresh_timer.stop()
        range_start = max(row_no - self._fetch_count // 3, 0)
        items = self._catalog_model.objects.get(
            self._db,
            where=self._where,
            limit=(range_start, self._fetch_count),
            select_related=True
        )
        now = time.time()
        expired_time = now - self._update_interval
        cache = self._cache
        # clean the cache of expired rows
        for _row_no in tuple(cache.keys()):
            if cache[_row_no][1] <= expired_time:
                cache.pop(_row_no)
        #print('for row_no, item in enumerate(items, range_start):')
        for _row_no, item in enumerate(items, range_start):
            cache[_row_no] = (item, now)
        self._refresh_timer.start(self._update_interval * 1000)
        return cache[row_no][0]

    def data(self, index, role):
        if index.isValid():
            style = self.column_styles[index.column()]
            data = style.data.get(role)

            if not callable(data):  # not a function to call
                return data

            item = self.item(index.row())
            value = getattr(item, style.field_name)

            return data(style, value)  # call the function

    def rowCount(self, parent):
        if self._row_count is None:  # cached row count; if it's not filled yet - fetch it from the db
            self._row_count = self._catalog_model.objects.get_count(self._db, where=self._where)
            #print('rowCount', _rowsCount)
        return self._row_count

    def columnCount(self, parent):
        return self._column_count

#    def flags(self, index):
#        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section_no, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            style = self.h_header_styles[section_no]
        elif orientation == QtCore.Qt.Vertical:
            style = self.v_header_style
        else:
            return None
        data = style.data.get(role)
        return data(style, section_no) if callable(data) else data
