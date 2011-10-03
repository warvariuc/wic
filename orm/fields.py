from decimal import Decimal
import inspect
import orm



class Column():
    '''Abstract DB column, supported natively by the DB.'''
    def __init__(self, name=None, primary=False, index=False, unique=False, **kwargs):
        self.name = name
        

class IntColumn(Column):
    '''INT column type.'''
    def __init__(self, name, bytesCount, autoincrement=False, **kwargs):
        super().__init__(name, **kwargs)
        self.bytesCount = bytesCount
        self.autoincrement = autoincrement


class CharColumn(Column):
    '''CHAR, VARCHAR'''
    def __init__(self, name, maxLength, hasFixedLength=False, **kwargs):
        super().__init__(name, **kwargs)
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
        self._initArgs = args # field will be initalized using these params later, when the class is created
        self._initKwargs = kwargs 

    def _init(self, fieldName, tableClass, column, defaultValue):
        '''This is called by the Table metaclass to initialize the Field after a Table subclass is created.'''
        self.table = tableClass
        self.name = fieldName
        self.column = column
        self.defaultValue = defaultValue
        del self._initArgs, self._initKwargs
            
    def _render(self, db=None): # db - not needed?
        return self.column.name
        
#    def validate(self, x):
#        '''This function is called just before writing the value to the DB.
#        If validation if not passed it raises ValidationError.'''
#        return True # dummy validator which is always passed 


#class TableIndex():
#    '''Defines an index.'''
#    def __init__(self, fields, type):
#        self.fields = fields # fields involded in this index
#        self.type = type # index type: unique, primary, etc.


class StringField(Field):
    def _init(self, fieldName, tableClass, maxLength, defaultValue=None):
        super()._init(fieldName, tableClass, CharColumn(fieldName, maxLength), defaultValue)
        self.maxLength = maxLength


class DecimalFieldI(Field):
    '''Decimals stored as 8 byte INT (up to 18 digits).
    TODO: DecimalFieldS - decimals stored as strings - unlimited number of digits.'''
    def _init(self, fieldName, tableClass, maxDigits, decimalPlaces, defaultValue):
        super()._init(fieldName, tableClass, IntColumn(fieldName, 8), defaultValue)
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
    def _init(self, fieldName, tableClass):
        super()._init(fieldName, tableClass, IntColumn(fieldName, 8, primary=True, autoincrement=True), None)
        

class ItemField(Field):
    '''Foreign key - stores id of a row in another table.'''
    def _init(self, fieldName, tableClass, referTable):
        super()._init(fieldName, tableClass, IntColumn(fieldName + '_id', 8), None)
        self.table = referTable # foreign key - referenced type of table
        
    def _cast(self, value):
        if isinstance(value, orm.Table):
            return value.id
        return value


class TableIdField(Field):
    '''This field stores id of a given table in this DB.'''
    def _init(self, fieldName, tableClass):
        super()._init(fieldName, tableClass, IntColumn(fieldName + '_tid', 2), None)
        
    def _cast(self, value):
        if isinstance(value, orm.Table) or (inspect.isclass(value) and issubclass(value, orm.Table)):
            return value._tableId # Table.tableIdField == Table -> Table.tableIdField == Table._tableId 
        return value


class AnyItemField(Field):
    '''This field stores id of a row of any table.'''
    def _init(self, fieldName, tableClass):
        super()._init(fieldName, tableClass, None, None)
            
        tableIdField = TableIdField()
        tableIdField._init(fieldName, tableClass)
        setattr(tableClass, tableIdField.name, tableIdField)
        
        itemIdField = ItemField()
        itemIdField._init(fieldName, tableClass, None)
        setattr(tableClass, fieldName, itemIdField)
        
        self.tableIdField = tableIdField
        self.itemIdField = itemIdField

    def _cast(self, value):
        if isinstance(value, orm.Table):
            return value.id
        return value

    def __eq__(self, other): 
        assert isinstance(other, orm.Table)
        return Expression('AND', 
                          Expression('EQ', self.tableIdField, other._tableId), 
                          Expression('EQ', self.itemIdField, other.id))


class ValidationError(Exception): # TODO: make a separate module validators
    '''This type of exception is raised when a validation didn't pass.'''

