"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import orm
from orm import Nil, Column


class Expression():
    """Expression - pair of operands and operation on them."""

    sort = 'ASC' # default sorting

    def __init__(self, operation, left = Nil, right = Nil, type = None, **kwargs):
        """Create an expression.
            @param operation: string with the name of DB operation
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
        self.sort = 'DESC'
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
        @param db: GenericAdapter subclass to use for rendering."""
        db = db or orm.GenericAdapter
        operation = getattr(db, self.operation) # get the operation function from adapter
        args = [arg for arg in (self.left, self.right) if arg is not Nil] # filter nil operands
        return operation(*args) # execute the operation

    def _cast(self, value):
        """Converts a value to Field's comparable type. Default implementation."""
        return value



class Field(Expression):
    """Generic ORM table field."""

    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop('name', None) # attribute name of the field
        self.table = kwargs.pop('table', None) # part of which table is this field
        self.label = kwargs.pop('label', None) # label (textual name) of this field
        self._initArgs = args # field will be initalized using these params later, when the class is created
        self._initKwargs = kwargs # for later _init
        orm._fieldsCount += 1 # tracking creation order
        self._orderNo = orm._fieldsCount

    def _init(self, column, defaultValue, index = ''):
        """This is called by the metaclass to initialize the Field after a Table subclass is created."""
        #del self._initArgs, self._initKwargs
        self.column = column
        self.defaultValue = defaultValue
        self.label = self.label or self.name.replace('_', ' ').capitalize()

        if index:
            self.table._indexes.append(orm.Index([self], index))

    def __str__(self, db = None):
        #db = db or orm.GenericAdapter # we do not use adapter here
        return '%s.%s' % (self.table, self.column.name)

    def __call__(self, value):
        """You can use Field()(value) to return a tuple for INSERT."""
        return (self, value)



class CharField(Field):
    def _init(self, maxLength, defaultValue = None, index = ''):
        super()._init(Column('CHAR', self, precision = maxLength, default = defaultValue), defaultValue, index)


class TextField(Field):
    def _init(self, defaultValue = None):
        super()._init(Column('TEXT', self, default = defaultValue), defaultValue, None)


class IntegerField(Field):
    def _init(self, maxDigits = 9, defaultValue = None, autoincrement = False, index = ''):
        self.maxDigits = maxDigits
        self.autoincrement = autoincrement
        super()._init(Column('INT', self, precision = self.maxDigits, unsigned = True, default = defaultValue,
                             autoincrement = autoincrement), defaultValue, index)


class DecimalField(Field):
    def _init(self, maxDigits, fractionDigits, defaultValue = None, index = ''):
        super()._init(Column('DECIMAL', self, precision = maxDigits, scale = fractionDigits, default = defaultValue), defaultValue, index)


class DateField(Field):
    def _init(self, defaultValue = None, index = ''):
        super()._init(Column('DATE', self, default = defaultValue), defaultValue, index)


class DateTimeField(Field):
    def _init(self, defaultValue = None, index = ''):
        super()._init(Column('DATETIME', self, default = defaultValue), defaultValue, index)



class IdField(Field):
    """Primary integer autoincrement key. ID - implicitly present in each table."""
    def _init(self):
        super()._init(Column('INT', self, precision = 9, unsigned = True, nullable = False, autoincrement = True), None, 'primary') # 9 digits - int32 - should be enough


class BooleanField(Field):
    def _init(self, defaultValue = None, index = ''):
        super()._init(Column('INT', self, precision = 1, default = defaultValue), defaultValue, index)


class RecordIdField(Field):
    """Foreign key - stores id of a row in another table."""
    def _init(self, referTable, index = ''):
        """
        @param referTable: a model class of which record is referenced
        @param index: True if simple index, otherwise string with index type ('index', 'unique')
        """
        self._referTable = referTable # foreign key - referenced type of table
        super()._init(Column('INT', self, precision = 9, unsigned = True), None, index) # 9 digits - int32 - should be enough

    @property
    def referTable(self):
        referTable = self._referTable
        if orm.isModel(referTable):
            return referTable
        assert isinstance(referTable, str), 'Otherwise it should be path to the Model'
        self._referTable = orm.getObjectByPath(referTable, self.table.__module__)
        return self._referTable

    def _cast(self, value):
        """Convert a value into another value which is ok for this Field."""
        try:
            return int(value)
        except ValueError:
            raise SyntaxError('Record ID must be an integer.')


class TableIdField(Field):
    """This field stores id of a given table in this DB."""
    def _init(self, index = ''):
        super()._init(Column('INT', self, precision = 5, unsigned = True), None, index)

    def _cast(self, value):
        if isinstance(value, orm.Model) or orm.isModel(value):
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
