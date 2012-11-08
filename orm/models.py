"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

import inspect
from datetime import datetime as DateTime, date as Date
from decimal import Decimal
import orm


class Join():
    """Object holding parameters for a join.
    """
    def __init__(self, model, on, type = ''):
        """
        @param model: table to join 
        @param on: join condition
        @param type: join type. if empty - INNER JOIN 
        """
        assert orm.isModel(model), 'Pass a model class.'
        assert isinstance(on, orm.Expression), 'WHERE should be an Expression.'
        self.model = model  # table to join
        self.on = on  # expression defining join condition
        self.type = type  # join type. if empty - INNER JOIN


class LeftJoin(Join):
    """Left join parameters.
    """
    def __init__(self, table, on):
        super().__init__(table, on, 'left')


class ModelBase(type):
    """Metaclass for all tables (models).
    It gives names to all fields and makes instances for fields for each of the models. 
    It has some class methods for models.
    """
    def __new__(cls, name, bases, attrs):
        NewModel = type.__new__(cls, name, bases, attrs)

        assert isinstance(NewModel._meta, model_options.ModelOptions), \
            '`_meta` attribute should be a ModelOptions instance'

#        if NewModel._meta.db_table is None:  # we need only Model subclasses
#            # if db table name is None - __new__ is called for Model itself
#            return NewModel  # return without any processing

        logger.debug('Finishing initialization of model `%s`' % orm.getObjectPath(NewModel))

        stubAttributes = []
        for attrName, attr in inspect.getmembers(NewModel):
            if isinstance(attr, fields.ModelAttrMixin):
                stubAttributes.append((attrName, attr))

        # sort by definition order - for the correct recreation order
        stubAttributes.sort(key = lambda i: i[1]._creationOrder)

        for attrName, attr in stubAttributes:
            if isinstance(attr, fields.Field):
                # Field instances are special - we recreate them for each of the models
                # that inherited models would have there own field, not parent's
                attr = attr.__class__(*attr._initArgs, **attr._initKwargs)
            try:
                attr.__init__(modelAttrInfo=fields.ModelAttrInfo(NewModel, attrName))
            except Exception:
                logger.debug('Failed to init a model attribute: %s.%s'
                              % (NewModel.__name__, attrName))
                raise
            setattr(NewModel, attrName, attr)

        return NewModel

    def __getitem__(self, key):
        """Get a Table Field by name - Table['field_name'].
        """
        attr = getattr(self, key, None)
        if isinstance(attr, orm.fields.Field):
            return attr
        raise KeyError('Could not find field %s in table %s' % (key, self.__class__))

    def __iter__(self):
        """Get Table fields.
        """
        fields = []
        for attrName in self.__dict__:
            try:  # there maybe non Field attributes as well
                fields.append(self[attrName])
            except KeyError:
                pass
        fields.sort(key = lambda field: field._creationOrder)  # sort by creation order - because __dict__ is unordered
        for field in fields:
            yield field

    def __len__(self):
        return len(list(self.__iter__()))

    def __str__(self):
        return self._meta.db_name


from . import fields, signals, logger, exceptions, model_options, query_manager


class Model(metaclass = ModelBase):
    """Base class for all tables. Class attributes - the fields. 
    Instance attributes - the values for the corresponding table fields.
    """
    objects = query_manager.QueryManager()
    _meta = model_options.ModelOptions()

    # default fields
    id = fields.IdField()  # row id. This field is present in all tables
    timestamp = fields.DateTimeField()  # version of the record - datetime (with milliseconds) of the last update of this record

    def __init__(self, db, *args, **kwargs):
        """Create a model instance - a record.
        @param db: db adapter in which to save the table record or from which it was fetched
        @param *args: tuples (Field or field_name, value) 
        @param **kwargs: {fieldName: fieldValue}
        """
        self._db = db

        table = None
        for arg in args:
            assert isinstance(arg, (list, tuple)) and len(arg) == 2, \
                'Pass tuples with 2 items: (field, value).'
            field, value = arg
            if isinstance(field, str):
                field = self.__class__[field]
            assert isinstance(field, fields.Field), 'First arg must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
            kwargs[field.name] = value

        for field in self.__class__:  # make values for fields
            setattr(self, field.name, kwargs.pop(field.name, field.default))

        if kwargs:
            raise NameError('Got unknown field names: %s' % ', '.join(kwargs))

    def __getitem__(self, field):
        """Get a Record Field value by key.
        key: either a Field instance or name of the field.
        """
        model = self.__class__
        if isinstance(field, fields.Field):
            assert field.table is model, 'This field is from another model.'
            attrName = field.name
        elif isinstance(field, str):
            field = model[field]
            attrName = field.name
        else:
            raise TypeError('Pass either a Field or its name.')
        return getattr(self, attrName)

    def delete(self):
        """Delete this record.
        """
        db = self._db
        self.checkTable(db)
        model = self.__class__
        signals.post_delete.send(sender = model, record = self)
        db.delete(model, where = (model.id == self.id))
        db.commit()
        self.id = None
        signals.post_delete.send(sender = model, record = self)

    def save(self):
        db = self._db
        self.checkTable(db)
        model = self.__class__
        self.timestamp = DateTime.now()
        values = []  # list of tuples (Field, value)
        for field in model:
            value = self[field]
            values.append(field(value))

        signals.pre_save.send(sender = model, record = self)

        isNew = not self.id
        if isNew:  # new record
            self.id = db.insert(*values)
        else:  # existing record
            rowsCount = db.update(*values, where = (model.id == self.id))
            if not rowsCount:
                raise orm.exceptions.SaveError(
                    'Looks like the record was deleted: table=`%s`, id=%s' % (model, self.id)
                )
        db.commit()

        signals.post_save.send(sender = model, record = self, isNew = isNew)

    def __str__(self):
        """Human readable presentation of the record.
        """
        values = []
        for field in self.__class__:
            value = getattr(self, field.name)
            if isinstance(value, (Date, DateTime, Decimal)):
                value = str(value)
            values.append("%s= %r" % (field.name, value))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(values))

    @classmethod
    def COUNT(cls, where = None):
        """Get COUNT expression for this table.
        @param where: WHERE expression
        """
        return orm.COUNT(where or cls)  # COUNT expression
