from decimal import Decimal
import inspect
import orm



class Column():
    '''Abstract DB column, supported natively by the DB.'''
    def __init__(self, name, field):
        self.name = name
        self.field = field 
        

class IntColumn(Column):
    '''INT column type.'''
    def __init__(self, name, field, bytesCount, autoincrement=False, **kwargs):
        super().__init__(name, field)
        self.bytesCount = bytesCount
        self.autoincrement = autoincrement


class CharColumn(Column):
    '''CHAR, VARCHAR'''
    def __init__(self, name, field, maxLength, hasFixedLength=False, **kwargs):
        super().__init__(name, field)
        self.maxLength = maxLength
        self.hasFixedLength = hasFixedLength
        

class BlobColumn(Column):
    '''BLOB'''


class TextColumn(Column):
    '''TEXT'''



class Nil(): '''Custom None'''
    

class Expression():
    def __init__(self, operation, left=Nil, right=Nil, type=None): # FIXME: type parameter not needed?
        self.operation = operation
        self.left = left # left operand
        self.right = right # right operand
        if left is not Nil and not type:
            if isinstance(left, Field):
                self.type = left
            elif isinstance(left, Expression):
                self.type = left.type
            else:
                raise Exception('Cast target must be an Expression/Field.')
        else:
            self.type = type
        
    def __and__(self, other): return Expression('AND', self, other)
    def __or__(self, other): return Expression('OR', self, other)
    def __eq__(self, other): return Expression('EQ', self, other)
    def __ne__(self, other): return Expression('NE', self, other)
    def __gt__(self, other): return Expression('GT', self, other)
    def __ge__(self, other): return Expression('GE', self, other)
    def __lt__(self, other): return Expression('LT', self, other)
    def __le__(self, other): return Expression('LE', self, other)
    def __add__(self, other): return Expression('ADD', self, other)
    def IN(self, *items):
        '''The IN clause.''' 
        return Expression('BELONGS', self, items)
    
    def _render(self, db=None):
        '''Construct the text of the WHERE clause from this Expression.
        db - db adapter to use for rendering. If None - use default.'''
        db = db or orm.defaultAdapter
        operation = self.operation
        operation = getattr(db, operation)
#        try:
#            operation = getattr(db, operation)
#        except AttributeError:
#            return '(%s)' % self.operation
            
        if self.right is not Nil:
            return operation(self.left, self.right)
        elif self.left is not Nil:
            return operation(self.left)
        return operation()

    def _cast(self, value):
        '''Converts a value to Field's comparable type. Default implementation.'''
        return value
    
#    def encode(self, x):
#        '''Function which processes the value before writing it to the DB'''
#        return x
#
#    def decode(self, x):
#        '''Function which processes the value after reading it from the DB'''
#        return x



class Field(Expression):
    '''ORM table field.'''
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop('name', None)
        self.table = kwargs.pop('table', None) # part of which table is this field
        self._initArgs = args # field will be initalized using these params later, when the class is created
        self._initKwargs = kwargs 

    def _init(self, column, defaultValue, index=''):
        '''This is called by the Table metaclass to initialize the Field after a Table subclass is created.'''
        del self._initArgs, self._initKwargs
        self.column = column
        self.defaultValue = defaultValue
        
        if index:
            self.table._indexes.append(orm.Index([self], index))
            
    def _render(self, adapter=None): # adapter - not needed?
        return self.column.name
    
    def __str__(self):
        return '{}.{}'.format(self.table.__name__, self.name)
        
#    def validate(self, x):
#        '''This function is called just before writing the value to the DB.
#        If validation if not passed it raises ValidationError.'''
#        return True # dummy validator which is always passed 


class StringField(Field):
    def _init(self, maxLength, defaultValue=None,  index=''):
        super()._init(CharColumn(self.name, self, maxLength), defaultValue, index)
        self.maxLength = maxLength


class IntegerField(Field):
    def _init(self, bytesCount, defaultValue=None, autoincrement=False, index=''):
        super()._init(IntColumn(self.name, self, bytesCount, autoincrement), defaultValue, index)
        self.bytesCount = bytesCount
        self.autoincrement = autoincrement


class DecimalFieldI(Field):
    '''Decimals stored as 8 byte INT (up to 18 digits).
    TODO: DecimalFieldS - decimals stored as strings - unlimited number of digits.'''
    def _init(self, maxDigits, decimalPlaces, defaultValue, index=''):
        super()._init(IntColumn(self.name, self, 8), defaultValue, index)
        self.maxDigits = maxDigits
        self.decimalPlaces = decimalPlaces
    
    def _cast(self, value):
        if isinstance(value, Field):
            if not isinstance(value, DecimalFieldI):
                raise SyntaxError('Only DecimalFieldI cooperands are supported.')
            if value.decimalPlaces != self.decimalPlaces:
                raise SyntaxError('Cooperand field must have the same number of decimal places.')
            return value
        return (Decimal(value) * (10 ** self.decimalPlaces)).normalize() # strip trailing zeroes after the decimal point

#    def encode(self, x):
#        '''Function which processes the value before writing it to the DB.'''
#        return int(x * (10 ** self.decimalPlaces))
#
#    def decode(self, x):
#        '''Function which processes the value after reading it from the DB'''
#        return Decimal(x / (10 ** self.decimalPlaces))


class IdField(Field):
    '''Built-in id type - for each table.'''
    def _init(self):
        super()._init(IntColumn(self.name, self, 8, autoincrement=True), None, 'primary')
        

class ItemField(Field):
    '''Foreign key - stores id of a row in another table.'''
    def _init(self, referTable, index=''):
        super()._init(IntColumn(self.name + '_id', self, 8), None, index)
        self.refTable = referTable # foreign key - referenced type of table
        
    def _cast(self, value):
        if isinstance(value, orm.Table):
            return value.id
        return value


class TableIdField(Field):
    '''This field stores id of a given table in this DB.'''
    def _init(self, index=''):
        super()._init(IntColumn(self.name + '_id', self, 2), None, index)
        
    def _cast(self, value):
        if isinstance(value, orm.Table) or (inspect.isclass(value) and issubclass(value, orm.Table)):
            return value._tableId # Table.tableIdField == Table -> Table.tableIdField == Table._tableId 
        return value


class AnyItemField(Field):
    '''This field stores id of a row of any table.'''
    def _init(self, index=''):
        super()._init(None, None) # no column, but later we create two fields
            
        tableIdField = TableIdField(name=self.name + '_tid', table=self.table)
        tableIdField._init()
        setattr(self.table, tableIdField.name, tableIdField)
        
        itemIdField = ItemField(name=self.name + '_id', table=self.table)
        itemIdField._init(None) # no refered table
        setattr(self.table, itemIdField.name, itemIdField)
        
        self.table._indexes.append(orm.Index([tableIdField, itemIdField], index))
        
        self._fields = dict(tableId=tableIdField, itemId=itemIdField)

    def _cast(self, value):
        if isinstance(value, orm.Table):
            return value.id
        return value

    def __eq__(self, other): 
        assert isinstance(other, orm.Table)
        return Expression('AND', 
                          Expression('EQ', self._fields['tableId'], other._tableId), 
                          Expression('EQ', self._fields['itemId'], other.id))

