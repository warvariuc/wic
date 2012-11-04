"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

import inspect
import copy
from datetime import datetime as DateTime, date as Date
from decimal import Decimal
from collections import OrderedDict
import orm
query_manager = orm.import_('orm.query_manager')
from . import fields, signals, logger, exceptions, model_options, query_manager


class Join():
    """Object holding parameters for a join.
    """
    def __init__(self, model, on, type = ''):
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


class ModelAttrInfo():
    """Information about an attribute of a Model
    """
    def __init__(self, model, attrName):
        assert orm.isModel(model)
        assert isinstance(attrName, str) and attrName
        assert hasattr(model, attrName)
        self.model = model
        self.attrName = attrName


class ModelAttrStub():
    """Temporary attribute for a Model, which holds information about what object with which
    initialization arguments should be put instead of it, after the model is completely defined.
    It's created by a Model attribute in its `__new__` method and replaced with a real object by the
    Model metaclass using `createObject` method.
    """
    __creationCounter = 0 # will be used to track the definition order of the attributes in models 

    def __init__(self, cls, args, kwargs):
        """
        @param cls: class of the object to be created after the Model is completely defined
        @param args: object initilization arguments 
        @param kwargs: object initilization keyword arguments
        """
        self.cls = cls
        self.args = args
        self.kwargs = kwargs
        # track creation order
        ModelAttrStub.__creationCounter += 1
        self.creationOrder = ModelAttrStub.__creationCounter

    def createObject(self, modelAttrInfo):
        """Create and return a real object instance using the initialization arguments supplied
        earlier. Usually called by the Model metaclass, after the model was already completely
        defined.
        @param modelAttrInfo: ModelAttrInfo instance which holds info about the model the real
            object belongs to and object attribute name.
        """
        assert isinstance(modelAttrInfo, ModelAttrInfo)
        return self.cls(*self.args, modelAttrInfo = modelAttrInfo, **self.kwargs)


class ModelAttrStubMixin():

    def __new__(cls, *args, modelAttrInfo = None, **kwargs):
        """Return a ModelAttributeStub instance if `model` argument is not there (meaning that the
        model is not yet completely defined), otherwise do it as usually.
        """
        if not modelAttrInfo:
            return ModelAttrStub(cls, args, kwargs)

        assert isinstance(modelAttrInfo, ModelAttrInfo)
        # create the object normally
        return super().__new__(cls, *args, modelAttrInfo = modelAttrInfo, **kwargs)
    

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

        stubAttributes = {}
        for attrName, attr in inspect.getmembers(NewModel):
            if isinstance(attr, ModelAttrStub):
                stubAttributes[attrName] = attr
            elif isinstance(attr, orm.Field):
                subclassField = copy.deepcopy(attr)
                subclassField.model= NewModel
                setattr(NewModel, attrName, subclassField)
                
        # sort by definition order (as __dict__ is unsorted) - for the correct recreation order
        stubAttributes = OrderedDict(sorted(stubAttributes.items(),
                                            key = lambda i: i[1].creationOrder))

        for stubAttrName, stubAttr in stubAttributes.items():
            try:
                realObject = stubAttr.createObject(ModelAttrInfo(NewModel, stubAttrName))
            except Exception:
                print('Failed to init a model attribute:', stubAttrName)
                raise
            setattr(NewModel, stubAttrName, realObject)

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
            try: # there maybe non Field attributes as well
                fields.append(self[attrName])
            except KeyError:
                pass
        fields.sort(key = lambda field: field._id) # sort by creation order - because __dict__ is unordered
        for field in fields:
            yield field

    def __len__(self):
        return len(list(self.__iter__()))

    def __str__(self):
        return self._meta.db_name



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
