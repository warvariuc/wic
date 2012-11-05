__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from datetime import datetime as DateTime, date as Date
from decimal import Decimal
import sys

import orm
from orm import Nil, logger
from . import adapters, indexes


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
    __creationCounter = 0  # will be used to track the definition order of the attributes in models 

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
        try:
            return self.cls(*self.args, modelAttrInfo = modelAttrInfo, **self.kwargs)
        except Exception:
            print('Failed to create a real object of class %r from stub' % self.cls, self.args, modelAttrInfo, self.kwargs)
            raise


def isStubInstance(obj, cls):
    return isinstance(obj, cls) or (isinstance(obj, ModelAttrStub) and issubclass(obj.cls, cls))


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


class Expression():
    """Expression - pair of operands and operation on them.
    """

    sort = 'ASC'  # default sorting

    def __init__(self, operation, left = Nil, right = Nil, type = None, **kwargs):
        """Create an expression.
        @param operation: string with the operation name (defined in adapters) 
        @param left: left operand
        @param right: right operand
        @param type: cast type field
        """
        if left is not Nil and not type:
            if isinstance(left, Field):
                self.type = left
            elif isinstance(left, Expression):
                self.type = left.type
            else:
                self.type = None
                #left = str(left)
                #raise Exception('Cast target must be an Expression/Field.')
        else:
            self.type = type
        self.operation = operation
        self.left = left  # left operand
        self.right = right  # right operand
        self.__dict__.update(kwargs)  # additional arguments

    def __and__(self, other):
        return Expression('_AND', self, other)
    def __or__(self, other):
        return Expression('_OR', self, other)
    def __eq__(self, other):
        return Expression('_EQ', self, other)
    def __ne__(self, other):
        return Expression('_NE', self, other)
    def __gt__(self, other):
        return Expression('_GT', self, other)
    def __ge__(self, other):
        return Expression('_GE', self, other)
    def __lt__(self, other):
        return Expression('_LT', self, other)
    def __le__(self, other):
        return Expression('_LE', self, other)
    def __add__(self, other):
        return Expression('_ADD', self, other)

    def __neg__(self):
        """-Field: sort DESC"""
        self.sort = 'DESC'  # TODO: should return new Expression
        return self
    def __pos__(self):
        """+Field: sort ASC"""
        self.sort = 'ASC'
        return self

    def UPPER(self):
        return Expression('_UPPER', self)

    def LOWER(self):
        return Expression('_LOWER', self)

    def IN(self, *items):
        """The IN clause."""
        return Expression('_IN', self, items)

    def LIKE(self, pattern):
        assert isinstance(pattern, str), 'Pattern must be a string.'
        return Expression('_LIKE', self, pattern)

    def __str__(self, db = None):
        """Construct the text of the WHERE clause from this Expression.
        @param db: GenericAdapter subclass to use for rendering.
        """
        args = [arg for arg in (self.left, self.right) if arg is not Nil]  # filter nil operands
        if not args:  # no args - treat operation as representation of the entire operation
            return self.operation
        db = db or orm.GenericAdapter
        operation = getattr(db, self.operation)  # get the operation function from adapter
        return operation(*args)  # execute the operation

    def cast(self, value):
        """Converts a value to Field's comparable type. Default implementation.
        """
        return value


class Field(Expression, ModelAttrStubMixin):
    """Abstract ORM table field.
    """
    def __init__(self, modelAttrInfo, column, index = '', label = '', db_name = ''):
        """Base initialization method. Called from subclasses.
        @param column: Column instance
        @param index: 
        """
        assert isinstance(modelAttrInfo, ModelAttrInfo)
        self.model = modelAttrInfo.model
        self.name = modelAttrInfo.attrName
        if not self.name.islower() or self.name.startswith('_'):
            raise orm.ModelError('Field `%s` in model `%s`: field names must be lowercase and '
                                 'must not start with `_`.' % (self.name, self.model))
        assert isinstance(column, adapters.Column)
        self.column = column
        assert isinstance(index, (str, bool, indexes.Index))
        self.index = index
        assert isinstance(label, str)
        self.label = label or self.name.replace('_', ' ').capitalize()

    def __str__(self, db = None):
        #db = db or orm.GenericAdapter # we do not use adapter here
        return '%s.%s' % (self.model, self.column.name)

    def __call__(self, value):
        """You can use Field(...)(value) to return a tuple for INSERT.
        """
        return (self, value)

####################################################################################################

class IdField(Field):
    """Primary integer autoincrement key. ID - implicitly present in each table.
    """
    def __init__(self, db_name = '', label = '', modelAttrInfo = None):
        super().__init__(
            modelAttrInfo,
            # 9 digits - int32 - should be enough
            adapters.Column('INT', precision = 9, unsigned = True, nullable = False,
                   autoincrement = True),
            'primary', label, db_name = db_name)

    def __set__(self, record, value):
        record.__dict__[self.name] = None if value is None else int(value)


class CharField(Field):
    """Field for storing strings of certain length.
    """
    def __init__(self, maxLength, default = None, index = '', db_name = '', label = '',comment = '',
               modelAttrInfo = None):
        """Initialize a CHAR field.
        @param maxLength: maximum length in bytes of the string to be stored in the DB
        @param default: default value to store in the DB
        @param index: index type to be applied on the corresponding column in the DB
        @param name: name of the column in the DB table
        @param label: short description of the field (e.g.for for forms)
        @param comment: comment for the field
        """
        super().__init__(
            modelAttrInfo,
            adapters.Column('CHAR', precision = maxLength, default = default, comment = comment),
            index, label, db_name = db_name)


class TextField(Field):
    """Field for storing strings of any length."""
    def __init__(self, default = None, index = '', db_name = '', label = '', modelAttrInfo = None):
        if index:
            assert isinstance(index, orm.Index)
        super().__init__(modelAttrInfo, adapters.Column('TEXT', default = default),
                         index, label, db_name = db_name)


class IntegerField(Field):

    def __init__(self, maxDigits = 9, default = None, autoincrement = False, index = '',
                 label = '', modelAttrInfo = None):
        super().__init__(
            modelAttrInfo,
            adapters.Column('INT', precision = self.maxDigits, unsigned = True, default = default,
                   autoincrement = autoincrement),
            index, label
        )

    def __set__(self, record, value):
        record.__dict__[self.name] = int(value)


class DecimalField(Field):

    def __init__(self, maxDigits, fractionDigits, default = None, index = '', label = '',
                 modelAttrInfo = None):
        super().__init__(
            modelAttrInfo,
            adapters.Column('DECIMAL', precision = maxDigits, scale = fractionDigits,
                   default = default),
            index, label)

    def __set__(self, record, value):
        record.__dict__[self.name] = None if value is None else Decimal(value)


class DateField(Field):

    def __init__(self, default = None, index = '', label = '', modelAttrInfo = None):
        super().__init__(modelAttrInfo, adapters.Column('DATE', default = default), index, label)

    def __set__(self, record, value):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d').date()
        elif not isinstance(value, Date) and value is not None:
            raise ValueError('Provide a datetime.date or a string in format "%Y-%m-%d" with valid '
                             'date.')
        record.__dict__[self.name] = value


class DateTimeField(Field):

    def __init__(self, default = None, index = '', label = '', modelAttrInfo = None):
        super().__init__(modelAttrInfo, adapters.Column('DATETIME', default = default), index, label)

    def __set__(self, record, value):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        elif not isinstance(value, DateTime) and value is not None:
            raise ValueError('Provide a datetime.datetime or a string in format '
                             '"%Y-%m-%d %H:%M:%S.%f" with valid date-time.')
        record.__dict__[self.name] = value


class BooleanField(Field):

    def __init__(self, default = None, index = '', label = '', modelAttrInfo = None):
        super()._init_(
            modelAttrInfo, adapters.Column('INT', precision = 1, default = default), index, label)

    def __set__(self, record, value):
        record.__dict__[self.name] = None if value is None else bool(value)


class _RecordId(int):
    """Keeps id of a referred record allowing to get the referred record.
    """
    def __new__(cls, *args, recordIdField, record, **kwargs):
        """
        @param recordIdField: referred record id model field - to know which model is referred
        @param record: record part of which is this referred record id
        """
        self = super().__new__(cls, *args, **kwargs)
        self._recordIdField = recordIdField
        self._record = record
        return self

    @property
    def record(self):
        "Get the record referred by this id."
        return getattr(self._record, self._recordIdField.referRecordAttrName)


class RecordField(Field):
    """Field for storing ids to referred records.
    """
    def __init__(self, referTable, index = '', label = '', modelAttrInfo = None):
        """
        @param referTable: a Model subclass of which record is referenced
        @param index: True if simple index, otherwise string with index type ('index', 'unique')
        """
        assert isinstance(modelAttrInfo, ModelAttrInfo)
        super().__init__(
            modelAttrInfo,
            # 9 digits - int32 - ought to be enough for anyone ;)
            adapters.Column('INT', name = modelAttrInfo.attrName + '_id', precision = 9, unsigned = True),
            index, label)
        self._referTable = referTable  # path to the model
        self._name = '__' + self.name  # name of the attribute which keeps the referred record or its id

    def __get__(self, record, model):
        if record is None:  # called as a class attribute
            return self
        # called as an instance attribute
        referRecord = getattr(record, self._name)
        if referRecord is None:
            return None
        elif isinstance(referRecord, self.referTable):
            return referRecord
        elif isinstance(referRecord, int):
            referRecord = self.referTable.getOne(record._db, id = referRecord)
            setattr(record, self._name, referRecord)
            return referRecord
        else:
            raise TypeError('This should not have happened: private attribute is not a record of '
                            'required model, id or None')

    def __set__(self, record, value):
        """You can assign to the field an integer id or the record itself."""
        assert isinstance(value, (int, self.referTable)) or value is None, \
            'You can assign only records of model `%s`, an integer id of the record or None' \
            % self.referTable
        setattr(record, self._name, value)  # _name will contain the referred record

    @orm.LazyProperty
    def referTable(self):
        if orm.isModel(self._referTable):
            return self._referTable
        elif isinstance(self._referTable, str):
            return orm.getObjectByPath(self._referTable, self.table.__module__)
        else:
            raise exceptions.ModelError('Referred model must be a Model or a string with its path.')

    def cast(self, value):
        """Convert a value into another value which is ok for this Field.
        """
        if isinstance(value, self.referTable):
            return value.id
        try:
            return int(value)
        except ValueError:
            raise exceptions.QueryError('Record ID must be an integer.')


#class TableIdField(Field):
#    """This field stores id of a given table in this DB."""
#    def _init_(self, index = ''):
#        super()._init_(Column('INT', self, precision = 5, unsigned = True), None, index)
#
#    def cast(self, value):
#        if isinstance(value, (orm.Model, orm.ModelMeta)):
#            return value._tableId # Table.tableIdField == Table -> Table.tableIdField == Table._tableId 
#        try:
#            return int(value)
#        except ValueError:
#            raise SyntaxError('Table ID must be an integer.')
#
#class AnyRecordField(Field):
#    """This field stores id of a row of any table.
#    It's a virtual field - it creates two real fields: one for keeping Record ID and another one for Table ID."""
#    def _init(self, index= ''):
#        super()._init(None, None) # no column, but later we create two fields
#            
#        tableIdField = TableIdField(name= self.name + '_table', table= self.table)
#        tableIdField._init()
#        setattr(self.table, tableIdField.name, tableIdField)
#        
#        recordIdField = RecordIdField(name= self.name + '_record', table= self.table)
#        recordIdField._init(None) # no refered table
#        setattr(self.table, recordIdField.name, recordIdField)
#        
#        self.table._indexes.append(orm.Index([tableIdField, recordIdField], index))
#        
#        self._fields = dict(tableId= tableIdField, itemId= recordIdField) # real fields
#
#    def __eq__(self, other): 
#        assert isinstance(other, orm.Model)
#        return Expression('AND', 
#                  Expression('EQ', self._fields['tableId'], other._tableId), 
#                  Expression('EQ', self._fields['itemId'], other.id))


def COUNT(expression = None, distinct = False):
    if expression is None or isinstance(expression, Expression):
        return Expression('_COUNT', None, distinct = distinct)
    elif orm.isModel(expression):
        return Expression('_COUNT', None, table = expression)
    else:
        raise orm.QueryError('Argument must be a Field, an Expression or a Table.')

def MAX(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_MAX', expression)

def MIN(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_MIN', expression)

def UPPER(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_UPPER', expression)

def LOWER(expression):
    assert isinstance(expression, Expression), 'Argument must be a Field or an Expression.'
    return Expression('_LOWER', expression)

def CONCAT(*expressions):
    "Concatenate two or more expressions/strings."
    for expression in expressions:
        assert isinstance(expression, (str, Expression)), \
            'Argument must be a Field or an Expression or a str.'
    return Expression('_CONCAT', expressions)


from . import models, model_options, exceptions
