__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

from datetime import datetime as DateTime, date as Date
from decimal import Decimal
import orm
from orm import Nil, Column, logger


class Expression():
    """Expression - pair of operands and operation on them.
    """

    sort = 'ASC' # default sorting

    def __init__(self, operation, left = Nil, right = Nil, type = None, **kwargs):
        """Create an expression.
        @param operation: string with the operation name (defined in adapters) 
        @param left: left operand
        @param right: right operand 
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
        self.left = left # left operand
        self.right = right # right operand
        self.__dict__.update(kwargs) # additional arguments

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
        self.sort = 'DESC' # TODO: should return new Expression
        return self
    def __pos__(self):
        """+Field: sort ASC"""
        self.sort = 'ASC'
        return self

    def IN(self, *items):
        """The IN clause."""
        return Expression('_IN', self, items)

    def __str__(self, db = None):
        """Construct the text of the WHERE clause from this Expression.
        @param db: GenericAdapter subclass to use for rendering.
        """
        db = db or orm.GenericAdapter
        operation = getattr(db, self.operation) # get the operation function from adapter
        args = [arg for arg in (self.left, self.right) if arg is not Nil] # filter nil operands
        return operation(*args) # execute the operation

    def cast(self, value):
        """Converts a value to Field's comparable type. Default implementation.
        """
        return value



class Field(Expression):
    """Abstract ORM table field.
    """
    _fieldsCount = 0 # will be used to track the original definition order of the fields 

    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop('name', None) # attribute name of the field
        self.table = kwargs.pop('table', None) # part of which table is this field
        self.label = kwargs.pop('label', None) # label (textual name) of this field
        self._initArgs = args # field will be initalized using these params later, when the class is created
        self._initKwargs = kwargs # for later _init
        Field._fieldsCount += 1
        self._id = Field._fieldsCount # creation order

    def _init_(self, column, default, index = ''):
        """This is called by the metaclass to initialize the Field after a Table subclass is created."""
        #del self._initArgs, self._initKwargs
        self.column = column
        self.default = default
        self.label = self.label or self.name.replace('_', ' ').capitalize()

        if index: # index type name is given
            self.table._indexes.append(orm.Index([orm.IndexField(self)], index))

    def __str__(self, db = None):
        #db = db or orm.GenericAdapter # we do not use adapter here
        return '%s.%s' % (self.table, self.column.name)

    def __call__(self, value):
        """You can use Field()(value) to return a tuple for INSERT.
        """
        return (self, value)



class CharField(Field):
    """Field for storing strings of certain length.
    """
    def _init_(self, maxLength, default = None, index = ''):
        super()._init_(Column('CHAR', self, precision = maxLength, default = default), default, index)


class TextField(Field):
    """Field for storing strings of any length."""
    def _init_(self, default = None):
        super()._init_(Column('TEXT', self, default = default), default, None)


class IntegerField(Field):

    def _init_(self, maxDigits = 9, default = None, autoincrement = False, index = ''):
        self.maxDigits = maxDigits
        self.autoincrement = autoincrement
        super()._init_(Column('INT', self, precision = self.maxDigits, unsigned = True, default = default,
                             autoincrement = autoincrement), default, index)

    def __set__(self, record, value):
        record.__dict__[self.name] = int(value)


class DecimalField(Field):

    def _init_(self, maxDigits, fractionDigits, default = None, index = ''):
        super()._init_(Column('DECIMAL', self, precision = maxDigits, scale = fractionDigits, default = default), default, index)

    def __set__(self, record, value):
        record.__dict__[self.name] = None if value is None else Decimal(value)


class DateField(Field):

    def _init_(self, default = None, index = ''):
        super()._init_(Column('DATE', self, default = default), default, index)

    def __set__(self, record, value):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d').date()
        elif not isinstance(value, Date) and value is not None:
            raise ValueError('Provide a datetime.date or a string in format "%Y-%m-%d" with valid date.')
        record.__dict__[self.name] = value


class DateTimeField(Field):

    def _init_(self, default = None, index = ''):
        super()._init_(Column('DATETIME', self, default = default), default, index)

    def __set__(self, record, value):
        if isinstance(value, str):
            value = DateTime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
        elif not isinstance(value, DateTime) and value is not None:
            raise ValueError('Provide a datetime.datetime or a string in format "%Y-%m-%d %H:%M:%S.%f" with valid date-time.')
        record.__dict__[self.name] = value


class IdField(Field):
    """Primary integer autoincrement key. ID - implicitly present in each table.
    """
    def _init_(self):
        super()._init_(Column('INT', self, precision = 9, unsigned = True, nullable = False, autoincrement = True), None, 'primary') # 9 digits - int32 - should be enough

    def __set__(self, record, value):
        record.__dict__[self.name] = None if value is None else int(value)


class BooleanField(Field):

    def _init_(self, default = None, index = ''):
        super()._init_(Column('INT', self, precision = 1, default = default), default, index)

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


class RecordIdField(Field):
    """Foreign key - stores id of a row in another table.
    """
    def _init_(self, referTable, index = ''):
        """
        @param referTable: a model class of which record is referenced
        @param index: True if simple index, otherwise string with index type ('index', 'unique')
        """
        if not self.name.endswith('_id'):
            raise orm.ModelError('RecordIdField name should end with `_id` (`%s.%s`)' % (self.table, self.name))

        self.referRecordAttrName = self.name[:-3] # name with '_id' stripped 
        if self.referRecordAttrName in self.table.__dict__:
            raise orm.ModelError('There is an attribute with name `%s` which clashes with RecordIdField name `%s.%s`.'
                                 'That name is reserved for the record referenced by that record id.' % (self.referRecordAttrName, self.table, self.name))

        if orm.isModel(referTable):
            self.__dict__['referTable'] = referTable # override the descriptor
        elif not isinstance(referTable, str):
            raise orm.ModelError('Referred model must be a Model or a string with its path.')
        else:
            self._referTable = referTable # path to the model

        self._name = '__' + self.name[:-3] # name of the attribute which keeps the referred record or its id

        super()._init_(Column('INT', self, precision = 9, unsigned = True), None, index) # 9 digits - int32 - ought to be enough for anyone ;)

        # create the proxy descriptor for the record referenced by the id field
        setattr(self.table, self.referRecordAttrName, ReferredRecord(self))

    def __get__(self, record, model = None):
        if record: # called as an instance attribute
            assert isinstance(record, orm.Model), 'This descriptor is only for Model instances!'
            referRecord = getattr(record, self._name) # id or the referred record itself
            if referRecord is None:
                return None
            elif isinstance(referRecord, self.referTable): # last assigned value was Record
                if referRecord.id is None:
                    return None
                return _RecordId(referRecord.id, record = record, recordIdField = self)
            elif isinstance(referRecord, int): # last assigned value was id
                return _RecordId(referRecord, record = record, recordIdField = self)
            else:
                raise TypeError('This should not have happened: private attribute is not a record of required model, int or None')
        else: # called as a class attribute
            return self

    def __set__(self, record, value):
        setattr(record, self._name, None if value is None else int(value)) # _name will contain the id of the referred record

    @orm.LazyProperty
    def referTable(self):
        return orm.getObjectByPath(self._referTable, self.table.__module__)

    def cast(self, value):
        """Convert a value into another value which is ok for this Field.
        """
        try:
            return int(value)
        except ValueError:
            raise orm.QueryError('Record ID must be an integer.')


class ReferredRecord():
    """Descriptor for proxying access to a referred record.
    """
    def __init__(self, recordIdField):
        """
        @param recordIdField: the paired IdField instance for hooking
        """
        assert isinstance(recordIdField, RecordIdField), 'orm.IdField instance is expected'
        logger.debug('Creating descriptor for %s' % recordIdField.name)
        self._recordIdField = recordIdField

    def __get__(self, record, model = None):
        if record: # called as an instance attribute
            assert isinstance(record, orm.Model), 'This descriptor is only for Model instances!'
            recordIdField = self._recordIdField
            referRecord = getattr(record, recordIdField._name)
            if referRecord is None:
                return None
            elif isinstance(referRecord, recordIdField.referTable):
                return referRecord
            elif isinstance(referRecord, int):
                referRecord = recordIdField.referTable.getOne(record._db, id = referRecord)
                setattr(record, recordIdField._name, referRecord)
                return referRecord
            else:
                raise TypeError('This should not have happened: private attribute is not a record of required model, id or None')
        else: # called as a class attribute
            return self

    def __set__(self, record, value):
        """When replacing refered record, its id is replacing the id kept in this record"""
        assert isinstance(record, orm.Model), 'This descriptor is only for Model classes!'
        recordIdField = self._recordIdField
        assert isinstance(value, recordIdField.referTable) or value is None, 'You can assign only records of model `%s`' % recordIdField.referTable
        setattr(record, recordIdField._name, value) # _name will contain the referred record



class TableIdField(Field):
    """This field stores id of a given table in this DB."""
    def _init_(self, index = ''):
        super()._init_(Column('INT', self, precision = 5, unsigned = True), None, index)

    def cast(self, value):
        if isinstance(value, (orm.Model, orm.ModelMeta)):
            return value._tableId # Table.tableIdField == Table -> Table.tableIdField == Table._tableId 
        try:
            return int(value)
        except ValueError:
            raise SyntaxError('Table ID must be an integer.')


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
    assert expression is None or isinstance(expression, Expression) or orm.isModel(expression), 'Argument must be a Field, an Expression or a Table.'
    return Expression('_COUNT', expression, distinct = distinct)

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
