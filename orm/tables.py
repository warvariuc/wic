import inspect
import orm


class TableMeta(type):
    '''Metaclass for all tables.'''
    
    def __new__(cls, name, bases, attrs):
        newClass = type.__new__(cls, name, bases, attrs)
        
        if 'Table' in globals(): # only Table subclasses. if Table is not defined - __new__ is called for it
            if not hasattr(newClass, '_tableId'):
                raise Exception('Table ID not set in {}!'.format(newClass))
            
            newClass._indexes = list(newClass._indexes) # assure each class has its own attribute
            for index in newClass._indexes :
                assert isinstance(index, Index), 'Found a non Index in the _indexes.'
                
            fields = [(fieldName, field) for fieldName, field in inspect.getmembers(newClass)
                        if isinstance(field, orm.fields.Field)]
            fields.sort(key=lambda f: f[1]._orderNo)
            
            for fieldName, field in fields:
                if not fieldName.islower() or fieldName.startswith('_'):
                    raise Exception('Field `{}` in Table `{}`: field names must be lowercase and must not start with `_`.'.format(fieldName, name))
                field_ = field.__class__() # recreate the field - to handle correctly inheritance of Tables
                field_.name = fieldName
                field_.table = newClass
                field_._init(*field._initArgs, **field._initKwargs) # and initialize it
                setattr(newClass, fieldName, field_) # each class has its own field object. Inherited and parent tables do not share field attributes
                    
        return newClass

    def __getitem__(self, key):
        '''Get a Table Field by name - Table['field_name'].'''
        attr = getattr(self, key, None)
        if isinstance(attr, orm.fields.Field):
            return attr
        raise KeyError('Could not find field {} in table {}'.format(key, self.__name__))
        
                 
    def __iter__(self):
        '''Get Table fields.'''
        fields = []
        for attrName in self.__dict__:
            try:
                fields.append(self[attrName])
            except KeyError:
                pass 
        fields.sort(key=lambda field: field._orderNo)
        for field in fields:
            yield field

    def __str__(self):
        return self.__name__.lower() 


class Table(metaclass=TableMeta):
    '''Base class for all tables. Class attributes - the fields. 
    Instance of this class are WHERE queries on this table.'''
    id = orm.IdField() # this field is present in all tables
    _indexes = [] # each table subclass will have its own (metaclass will assure this)

    def __init__(self, expression):
        assert isinstance(expression, orm.fields.Expression)
        self.where = expression

    @classmethod
    def getCreateStatement(cls, adapter):
        '''CREATE TABLE statement for the given DB.'''
        return adapter.getCreateTableQuery(cls)
    
    @classmethod
    def new(cls, adapter, **kwargs):
        '''Create new item of this Table'''
        return Record(cls, adapter, **kwargs)
    
    @orm.class_or_instance_method
    def select(self, adapter, where=None, join=()):
        if where is None:
            assert isinstance(self, Table), 'Provide a WHERE expression.'
            where = self.where                
        assert isinstance(where, orm.fields.Expression)
        return []



class Record():
    '''Row/record of a Table - new or existing.'''
    def __init__(self, _table, _adapter, **kwargs):
        '''Initialize a new record of the given table in the given database.'''
        assert inspect.isclass(_table) and issubclass(_table, Table)
        
        self._table = _table
        self._adapter = _adapter # in which db?
        
        for field in _table: # make values for fields
            setattr(self, field.name, kwargs.pop(field.name, field.defaultValue))
    
    def delete(self):
        #self._table(self._table.id == self.id).delete(self._adapter)
        self._table(id=self.id).delete(self._adapter)
        
    def save(self):
        (self._table.id == self.id).update(self._adapter)

    def __str__(self):
        return '%s(%s)' % (self._table.__name__, 
            ', '.join('%s=%r' % (field.name, getattr(self, field.name))
                       for field in self._table)) 


class Index():
    '''Defines a DB table index.
    type: index, unique, fulltext, spatial
    sort: asc, desc
    method: btree, hash, gist, and gin'''
    def __init__(self, fields, type='index', name='', sortOrders=None, prefixLengths=None, method='', **kwargs):
        assert isinstance(fields, (list, tuple)), 'Pass a list of indexed fields.'
        assert fields, 'You did not indicate which fields to index.'
        table = fields[0].table
        for field in fields:
            assert isinstance(field, orm.fields.Field)
            if field.table is not table:
                raise AssertionError('Indexed fields should be from the same table!') 
        sortOrders = sortOrders or ['asc'] * len(fields) 
        prefixLengths = prefixLengths or [0] * (len(fields))
        assert isinstance(sortOrders, (list, tuple)), 'Sort orders must be a list.'
        assert isinstance(prefixLengths, (list, tuple)), 'Prefix lengths must be a list.'
        assert len(fields) == len(sortOrders) == len(prefixLengths), 'Lists of fields, sort orders and prefix lengths must be the same.'
        
        if type == True:
            type = 'index'
            
        if name == '':
            for field in fields:
                name += field.name + '_'
            name += type   
        self.name = name
        self.fields = fields # fields involved in this index
        self.type = type # index type: unique, primary, etc.
        self.prefixLengths = prefixLengths # prefix lengths
        self.sortOrders = sortOrders # sort direction: asc, desc
        self.method = method # if empty - will be used default for this type of DB
        self.other = kwargs # other parameters for a specific DB adapter
    
    def __str__(self):
        return '{} `{}` ON ({}) {}'.format(self.type, self.name, 
                            ', '.join(map(str, self.fields)), self.method)
