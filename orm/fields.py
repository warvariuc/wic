"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import orm


class Nil():
    """Custom None"""


class Column():
    """Abstract DB column, supported natively by the DB."""

    def __init__(self, type, field, name = ''):
        self.type = type
        self.field = field
        self.name = name or field.name



class Expression():
    """Expression - pair of operands and operation on them."""

    sort = 'ASC' # default sorting

    def __init__(self, operation, left = Nil, right = Nil, type = None, **kwargs): # FIXME: type parameter not needed?
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

    def _render(self, adapter):
        """Construct the text of the WHERE clause from this Expression.
        adapter - db adapter to use for rendering. If None - use default."""
        operation = getattr(adapter, self.operation)
        args = [arg for arg in (self.left, self.right) if arg is not Nil]
        return operation(*args)

    def _cast(self, value):
        """Converts a value to Field's comparable type. Default implementation."""
        return value



class Field(Expression):
    """ORM table field."""

    def __init__(self, *args, **kwargs):
        #print('Field.__init__', self.__class__, args, kwargs)
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

    def _render(self, adapter):
        return '%s.%s' % (self.table, self.column.name)

    def __str__(self):
        return '{}.{}'.format(self.table, self.name)

    def __call__(self, value):
        """You can use Field()(value) to return a tuple for INSERT."""
        return (self, value)



class CharField(Field):
    def _init(self, maxLength, defaultValue = None, index = ''):
        self.maxLength = maxLength
        super()._init(Column('CHAR', self), defaultValue, index)


class TextField(Field):
    def _init(self, defaultValue = None):
        super()._init(Column('TEXT', self), defaultValue, None)


class IntegerField(Field):
    def _init(self, maxDigits = 9, defaultValue = None, autoincrement = False, index = ''):
        self.maxDigits = maxDigits
        self.autoincrement = autoincrement
        super()._init(Column('INT', self), defaultValue, index)


class DecimalField(Field):
    def _init(self, maxDigits, fractionDigits, defaultValue = None, index = ''):
        self.maxDigits = maxDigits
        self.fractionDigits = fractionDigits
        super()._init(Column('DECIMAL', self), defaultValue, index)


class DateField(Field):
    def _init(self, defaultValue = None, index = ''):
        super()._init(Column('DATE', self), defaultValue, index)


class DateTimeField(Field):
    def _init(self, defaultValue = None, index = ''):
        super()._init(Column('DATETIME', self), defaultValue, index)



class IdField(Field):
    """Primary integer autoincrement key. ID - implicitly present in each table."""
    def _init(self):
        self.maxDigits = 9 # int32 - should be enough
        self.autoincrement = True
        super()._init(Column('INT', self), None, 'primary')


class BooleanField(Field):
    def _init(self, defaultValue = None, index = ''):
        self.maxDigits = 1
        super()._init(Column('INT', self), defaultValue, index)


class RecordIdField(Field):
    """Foreign key - stores id of a row in another table."""
    def _init(self, referTable, index = ''):
        self._referTable = referTable # foreign key - referenced type of table
        self.maxDigits = 9 # int32 - should be enough
        super()._init(Column('INT', self), None, index)

    def getReferTable(self):
        referTable = self._referTable
        if orm.isModel(referTable):
            return referTable
        assert isinstance(referTable, str) # otherwise it should be path to the Model
        self._referTable = orm.getObjectByPath(referTable, self.table.__module__)
        return self._referTable

    referTable = property(getReferTable)

    def _cast(self, value):
        """Convert a value into another value which is ok for this Field."""
        try:
            return int(value)
        except ValueError:
            raise SyntaxError('Record ID must be an integer.')


class TableIdField(Field):
    """This field stores id of a given table in this DB."""
    def _init(self, index = ''):
        self.maxDigits = 5
        super()._init(Column('INT', self), None, index)

    def _cast(self, value):
        if isinstance(value, orm.Model) or orm.isModel(value):
            return value._tableId # Table.tableIdField == Table -> Table.tableIdField == Table._tableId 
        return int(value)


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


def COUNT(expression, distinct = False):
    assert isinstance(expression, orm.Expression) or orm.isModel(expression), 'Argument must be a Field, an Expression or a Table.'
    return Expression('_COUNT', expression, distinct = distinct)

def MAX(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('_MAX', expression)

def MIN(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('_MIN', expression)

def UPPER(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('_UPPER', expression)

def LOWER(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('_LOWER', expression)
