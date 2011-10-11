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
                
            for fieldName, field in inspect.getmembers(newClass):
                if isinstance(field, orm.fields.Field):
                    if not fieldName.islower() or fieldName.startswith('_'):
                        raise Exception('Field `{}` in Table `{}`: field names must be lowercase and must not start with `_`.'.format(fieldName, name))
                    field_ = field.__class__() # recreate the field - to handle correctly inheritance
                    field_.name = fieldName
                    field_.table = newClass
                    field_._init(*field._initArgs, **field._initKwargs) # and initialize it
                    setattr(newClass, fieldName, field_) # each class has its own field object. Inherited and parent tables do not share field attributes
                    
        return newClass

    def __getitem__(self, key):
        '''Able to do Table['field_name'].'''
        attr = getattr(self, key, None)
        if isinstance(attr, orm.fields.Field):
            return attr
        raise KeyError('Could not find field {} in table {}'.format(key, self.__name__))
        
                 
    def __iter__(self):
        for attrName in self.__dict__:
            try:
                yield self[attrName]
            except KeyError:
                pass 



class Table(metaclass=TableMeta):
    '''Base class for all tables. Class attributes - the fields. 
    Instance (item) attributes with the same names - the values for the corresponding fields.'''
    id = orm.IdField() # this field is present in all tables
    _indexes = [] # each table subclass will have its own (metaclass will assure this)

    def __init__(self, **kwargs):
        '''Initialize a new record of this table.'''
        self.adapter = kwargs.pop('db', orm.defaultAdapter) # in which db?
        
        # make values for fields 
        for fieldName, field in inspect.getmembers(self.__class__):
            if isinstance(field, orm.fields.Field):
                fieldValue = field._cast(kwargs.pop(fieldName, field.defaultValue))
                setattr(self, fieldName, fieldValue)
    
    def delete(self):
        (self.__class__.id == self.id).delete(self.adapter)
        
    def save(self):
        (self.__class__.id == self.id).update(self.adapter)

    def __iter__(self):
        for field in self.__class__:
            yield (field.name, getattr(self, field.name))
            
    @classmethod
    def getCreateStatement(cls, adapter):
        return adapter.getTableCreateStatement(cls)
    
    def __str__(self):
        return self.__class__.__name__ + '(' + \
            ', '.join('%s=%r' % value for value in self) + ')' 


class Index():
    '''Defines a DB table index.
    type: index, unique, fulltext, spatial
    method: btree, hash, gist, and gin'''
    def __init__(self, fields, type='index', name='', method='', prefixLength=None, **kwargs):
        assert isinstance(fields, (list, tuple)), 'Pass a list of indexed fields.'
        assert fields, 'You did not indicate which fields to index.'
        
        if type == True:
            type = 'index'
            
        if name == '':
            for field in fields:
                name += field.name + '_'
            name += type   
        self.name = name
        self.fields = fields # fields involved in this index
        self.type = type # index type: unique, primary, etc.
        self.method = method # if empty - will be used default for this type of DB
        self.__dict__.update(kwargs) # other parameters for a specific DB adapter
    
    def __str__(self):
        return '{} `{}` ON ({}) {}'.format(self.type, self.name, 
                            ', '.join(map(str, self.fields)), self.method)
