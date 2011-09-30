from decimal import Decimal
import orm


class DbField():
    '''Abstract DB field, supported natively by the DB.'''
    def __init__(self, name=None, **kwargs):
        self.name = name
    
        

class DbIntegerField(DbField):
    '''INT'''
    def __init__(self, name, bytesCount, **kwargs):
        super().__init__(name, **kwargs)
        self.bytesCount = bytesCount


class DbStringField(DbField):
    '''VARCHAR, CHAR'''
    def __init__(self, name, maxLength, hasFixedLength=False, **kwargs):
        super().__init__(name, **kwargs)
        self.maxLength = maxLength
        self.hasFixedLength = hasFixedLength
        

class DbBlobField(DbField):
    '''BLOB'''


class DbTextField(DbField):
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
        db = db or orm.defaultDbAdapter
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

    def _init(self, fieldName, tableClass, dbField, defaultValue):
        '''This is called by the Table metaclass to initialize the Field after a Table class is created.'''
        assert isinstance(dbField, DbField)
        self.table = tableClass
        self.name = fieldName
        dbFieldName = fieldName
        if isinstance(self, ReferenceField):
            dbFieldName += '_id'
        dbField.name = dbFieldName
        self.dbField = dbField
        self.defaultValue = defaultValue
            
    def _render(self, db=None):
        return self.dbField.name
        
#    def validate(self, x):
#        '''This function is called just before writing the value to the DB.
#        If validation if not passed it raises ValidationError.'''
#        return True # dummy validator which is always passed 


#class TableIndex():
#    '''Defines an index.'''
#    def __init__(self, fields, type):
#        self.fields = fields # fields involded in this index
#        self.type = type # index type: unique, primary, etc.

class IdField(Field):
    '''Built-in id type - for each table.'''
    def _init(self, fieldName, tableClass):
        super()._init(fieldName, tableClass, DbIntegerField(fieldName, 8, primary=True, autoincrement=True), None)
        

class StringField(Field):
    def _init(self, fieldName, tableClass, maxLength, defaultValue=None):
        super()._init(fieldName, tableClass, DbStringField(fieldName, maxLength), defaultValue)
        self.maxLength = maxLength

class DecimalFieldI(Field):
    '''Decimals stored as 8 byte INT (up to 18 digits).
    TODO: DecimalFieldS - decimals stored as strings - unlimited number of digits.'''
    def _init(self, fieldName, tableClass, maxDigits, decimalPlaces, defaultValue):
        
        super()._init(fieldName, tableClass, DbIntegerField(fieldName, 8), defaultValue)
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


class ReferenceField(Field):
    '''Foreign key - stores id of a record in another table.'''
    def _init(self, fieldName, tableClass, referencedTable, index=False):
        # if table is None - this field makes additional db field for holding table id
        super()._init(fieldName, tableClass, DbIntegerField(fieldName, 8), None)
        self.table = referencedTable # foreign key - referenced type of table
        
    def _cast(self, value):
        if isinstance(value, orm.Table):
            return value.id
        return value


class ReferenceField2(Field):
    '''Foreign key - stores id of a record in another table.'''
    def __init__(self, table, name=None, index=False):
        # if table is None - this field makes additional db field for holding table id
        if table is not None:
            assert issubclass(table, orm.tables.Table)
            
        tableId = DbIntegerField(name, 2) # two bytes for keeping id of a table in this DB
        itemId = DbIntegerField(name, 8)
        super().__init__(DbIntegerField(name, 8), None)
        self.table = table # foreign key - referenced type of table
        
    def _cast(self, value):
        if isinstance(value, orm.tables.Table):
            return value.id
        return value

    def __eq__(self, other): 
        #return Expression('EQ', self, other)
        assert isinstance(other, orm.Table)
        return Expression('AND', Expression('EQ', self.tableIdField, other._tableId), Expression('EQ', self.itemIdField, other.id))


class ValidationError(Exception):
    '''This type of exception is raised when a validation didn't pass.'''

