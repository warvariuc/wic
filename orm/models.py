__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import inspect
from datetime import datetime as DateTime, date as Date
from decimal import Decimal
import orm


class ModelAttrInfo():
    """Information about an attribute of a Model
    """
    def __init__(self, model, name):
        if model:
            assert orm.isModel(model)
            assert isinstance(name, str) and name
            assert hasattr(model, name), 'Model %s does not have an attribute with name %s' \
                % (orm.getObjectPath(model), name)
        self.model = model
        self.name = name


class ModelAttr():
    """Mixin class for Model attributes, which holds information about initialization arguments,
    `__init__` being called only after the model is completely defined.
    Usually `__init__` is called  by the Model metaclass.
    """
    __creationCounter = 0  # will be used to track the definition order of the attributes in models
    _modelAttrInfo = ModelAttrInfo(None, None)  # model attribute information, set by `_init_` 

    def __new__(cls, *args, **kwargs):
        """Create the object, but prevent calling its `__init__` method, montkey patching it with a
        stub, remembering the initizalization arguments. The real `__init__` can be called later.
        """
        if cls.__init__ != ModelAttr.__proxy__init__:
            cls.__orig__init__ = cls.__init__  # original __init__
            cls.__init__ = ModelAttr.__proxy__init__  # monkey patching with our version

        # create the object normally
        obj = super().__new__(cls)
        obj._initArgs = args
        obj._initKwargs = kwargs
        ModelAttr.__creationCounter += 1
        obj._creationOrder = ModelAttr.__creationCounter
#        print('ModelAttrMixin.__new__', cls)
        return obj

    def __proxy__init__(self, *args, **kwargs):
        """This will replace `__init__` method of a Model attribute, will remember initialization
        arguments and will call the original `__init__` when information about the model attribute
        is passed.
        """
#        print('ModelAttrStubMixin.__init__', self.__class__.__name__, args, kwargs)
        modelAttrInfo = kwargs.pop('modelAttrInfo', None)
        if modelAttrInfo:
            self._modelAttrInfo = modelAttrInfo
            self.__orig__init__(*self._initArgs, **self._initKwargs)



class ModelBase(type):
    """Metaclass for all tables (models).
    It gives names to all fields and makes instances for fields for each of the models. 
    It has some class methods for models.
    """
    def __new__(cls, name, bases, attrs):
        NewModel = super().__new__(cls, name, bases, attrs)

        assert isinstance(NewModel._meta, model_options.ModelOptions), \
            '`_meta` attribute should be a ModelOptions instance'

#        if NewModel._meta.db_table is None:  # we need only Model subclasses
#            # if db table name is None - __new__ is called for Model itself
#            return NewModel  # return without any processing

        logger.debug('Finishing initialization of model `%s`' % orm.getObjectPath(NewModel))

        _meta = None
        stubAttributes = []
        for attrName, attr in inspect.getmembers(NewModel):
            if isinstance(attr, ModelAttr):
                if attrName == '_meta':
                    assert isinstance(attr, model_options.ModelOptions), \
                        '`_meta` attribute should be instance of ModelOptions'
                    _meta = attr
                else:
                    stubAttributes.append((attrName, attr))

        assert _meta is not None, 'Could not find `_meta` attribute'
        # sort by definition order - for the correct recreation order
        stubAttributes.sort(key = lambda i: i[1]._creationOrder)

        for attrName, attr in stubAttributes:
            if attr._modelAttrInfo.model:
                attr = attr.__class__(*attr._initArgs, **attr._initKwargs)
            try:
                attr.__init__(modelAttrInfo = ModelAttrInfo(NewModel, attrName))
            except Exception:
                logger.debug('Failed to init a model attribute: %s.%s'
                              % (orm.getObjectPath(NewModel), attrName))
                raise
            setattr(NewModel, attrName, attr)

        # process _meta at the end, when all fields should have been initialized
        if _meta._modelAttrInfo.model is not None:  # inherited
            _meta = model_options.ModelOptions()  # override
        _meta.__init__(modelAttrInfo = ModelAttrInfo(NewModel, '_meta'))
        NewModel._meta = _meta

        return NewModel

    def __getitem__(self, key):
        """Get a Table Field by name - Table['field_name'].
        """
        attr = getattr(self, key, None)
        if isinstance(attr, fields.ModelField):
            return attr.field
        raise KeyError('Could not find field %s in table %s' % (key, orm.getObjectPath(self)))

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
            assert isinstance(field, fields.ModelField), 'First arg must be a Field.'
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
        if isinstance(field, fields.ModelField):
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
        signals.pre_delete.send(sender = model, record = self)
        db.delete(model, where = (model.id == self.id))
        db.commit()
        signals.post_delete.send(sender = model, record = self)
        self.id = None

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
