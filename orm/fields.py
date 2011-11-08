'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''

from decimal import Decimal
import orm


class Nil(): 
    '''Custom None'''
    

class Expression():
    '''Expression - pair of operands and operation on them.'''
    sort = 'ASC' # default sorting
    
    def __init__(self, operation, left= Nil, right= Nil, type= None, **kwargs): # FIXME: type parameter not needed?
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
        return Expression('AND', self, other)
    def __or__(self, other): 
        return Expression('OR', self, other)
    def __eq__(self, other): 
        return Expression('EQ', self, other)
    def __ne__(self, other): 
        return Expression('NE', self, other)
    def __gt__(self, other): 
        return Expression('GT', self, other)
    def __ge__(self, other): 
        return Expression('GE', self, other)
    def __lt__(self, other): 
        return Expression('LT', self, other)
    def __le__(self, other): 
        return Expression('LE', self, other)
    def __add__(self, other): 
        return Expression('ADD', self, other)
    
    def __neg__(self):
        '''-Field: sort DESC'''
        self.sort = 'DESC'
        return self
    def __pos__(self):
        '''+Field: sort ASC'''
        self.sort = 'ASC'
        return self
    
    def IN(self, *items):
        '''The IN clause.''' 
        return Expression('IN', self, items)
    
    def _render(self, adapter):
        '''Construct the text of the WHERE clause from this Expression.
        adapter - db adapter to use for rendering. If None - use default.'''
        operation = getattr(adapter, self.operation)
        args = [arg for arg in (self.left, self.right) if arg is not Nil]      
        return operation(*args)

    def _cast(self, value):
        '''Converts a value to Field's comparable type. Default implementation.'''
        return value
    


class Field(Expression):
    '''ORM table field.'''
    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop('name', None)
        self.table = kwargs.pop('table', None) # part of which table is this field
        self._initArgs = args # field will be initalized using these params later, when the class is created
        self._initKwargs = kwargs
        orm._fieldsCount += 1
        self._orderNo = orm._fieldsCount  

    def _init(self, column, defaultValue, index= ''):
        '''This is called by the Table metaclass to initialize the Field after a Table subclass is created.'''
        del self._initArgs, self._initKwargs
        self.column = column
        self.defaultValue = defaultValue
        
        if index:
            self.table._indexes.append(orm.Index([self], index))
            
    def _render(self, adapter=None): # adapter - not needed?
        return '%s.%s' % (self.table, self.column.name)
    
    def __str__(self):
        return '{}.{}'.format(self.table, self.name)
    
    def __call__(self, value):
        '''You can use Field()(value) to return a tuple for INSERT.'''
        return (self, value)
        

class StringField(Field):
    def _init(self, maxLength, defaultValue= None, index= ''):
        super()._init(orm.adapters.Column(self.name, 'char', self, maxLength= maxLength), 
                      defaultValue, index)
        self.maxLength = maxLength
    
    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self.maxLength)


class IntegerField(Field):
    def _init(self, bytesCount, defaultValue= None, autoincrement= False, index=''):
        super()._init(orm.adapters.Column(self.name, 'int', self, bytesCount= bytesCount, 
                                          autoincrement= autoincrement), defaultValue, index)
        self.bytesCount = bytesCount
        self.autoincrement = autoincrement


class DecimalFieldI(Field):
    '''Decimals stored as 8 byte INT (up to 18 digits).
    TODO: DecimalFieldS - decimals stored as strings - unlimited number of digits.'''
    def _init(self, maxDigits, decimalPlaces, defaultValue, index= ''):
        super()._init(orm.adapters.Column(self.name, 'int', self, bytesCount= 8), defaultValue, index)
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


class IdField(Field):
    '''ID - implicitly present in each table.'''
    def _init(self):
        super()._init(orm.adapters.Column(self.name, 'int', self, bytesCount= 8, autoincrement= True), None, 'primary')
        

class RecordIdField(Field):
    '''Foreign key - stores id of a row in another table.'''
    def _init(self, referTable, index= ''):
        super()._init(orm.adapters.Column(self.name, 'int', self, bytesCount= 8), None, index)
        self._referTable = referTable # foreign key - referenced type of table
        
    def getReferTable(self):
        if isinstance(self._referTable, orm.Model): 
            return self._referTable
        return orm.getObjectByPath(self._referTable, self.table.__module__)
    
    referTable = property(getReferTable)
        
    def _cast(self, value):
        '''Convert a value into another value which is ok for this Field.'''
        try:
            return int(value)
        except ValueError:
            raise SyntaxError('Record ID must be an integer.')


class TableIdField(Field):
    '''This field stores id of a given table in this DB.'''
    def _init(self, index= ''):
        super()._init(orm.adapters.Column(self.name, 'int', self, bytesCount= 2), None, index)
        
    def _cast(self, value):
        if isinstance(value, orm.Model) or orm.isModel(value):
            return value._tableId # Table.tableIdField == Table -> Table.tableIdField == Table._tableId 
        return int(value)


class AnyRecordField(Field):
    '''This field stores id of a row of any table.
    It's a virtual field - it creates two real fields: one for keeping Record ID and another one for Table ID.'''
    def _init(self, index= ''):
        super()._init(None, None) # no column, but later we create two fields
            
        tableIdField = TableIdField(name= self.name + '_table', table= self.table)
        tableIdField._init()
        setattr(self.table, tableIdField.name, tableIdField)
        
        recordIdField = RecordIdField(name= self.name + '_record', table= self.table)
        recordIdField._init(None) # no refered table
        setattr(self.table, recordIdField.name, recordIdField)
        
        self.table._indexes.append(orm.Index([tableIdField, recordIdField], index))
        
        self._fields = dict(tableId= tableIdField, itemId= recordIdField) # real fields

    def __eq__(self, other): 
        assert isinstance(other, orm.Model)
        return Expression('AND', 
                  Expression('EQ', self._fields['tableId'], other._tableId), 
                  Expression('EQ', self._fields['itemId'], other.id))


def COUNT(expression, distinct= False):
    assert isinstance(expression, orm.Expression) or orm.isModel(expression), 'COUNT argument must be a Field, an Expression or a Table.'
    return Expression('COUNT', expression, distinct= distinct)

def MAX(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('MAX', expression)

def MIN(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('MIN', expression)

def UPPER(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('UPPER', expression)

def LOWER(expression):
    assert isinstance(expression, orm.Expression), 'Argument must be a Field or an Expression.'
    return Expression('LOWER', expression)
