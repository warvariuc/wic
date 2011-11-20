'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''

import inspect
from datetime import datetime as DateTime
import orm
from orm import signals


class Index():
    '''Defines a DB table index.
    type: index, unique, fulltext, spatial
    sort: asc, desc
    method: btree, hash, gist, and gin'''
    def __init__(self, fields, type= 'index', name= '', sortOrders= None, prefixLengths= None, method='', **kwargs):
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

class Join():
    '''Object holding parameters for a join.'''
    def __init__(self, model, on, type= ''):
        assert orm.isModel(model), 'Pass a model class.'
        assert isinstance(on, orm.fields.Expression), 'WHERE should be an Expression.'
        self.model = model # table to join
        self.on = on # expression defining join condition
        self.type = type # join type. if empty - INNER JOIN


class LeftJoin(Join):
    '''Left join parameters.'''
    def __init__(self, table, on):
        super().__init__(table, on, 'left')
        


class ModelMeta(type):
    '''Metaclass for all tables (models).'''
    
    def __new__(cls, name, bases, attrs):
        newClass = type.__new__(cls, name, bases, attrs)
        
        try: # we need only Model subclasses
            Model
        except NameError: # if Model is not defined: __new__ is called for Model itself
            return newClass # return wihout any processing
        
        newClass._indexes = list(newClass._indexes) # assure each class has its own attribute
        for index in newClass._indexes :
            assert isinstance(index, Index), 'Found a non Index in the _indexes.'
            
        fields = []
        for fieldName, field in inspect.getmembers(newClass):
            if isinstance(field, orm.fields.Field):
                fields.append((fieldName, field)) 
                    
        fields.sort(key= lambda f: f[1]._orderNo) # sort by definition order (as __dict__ is unsorted) - for field recreation order
        
        for fieldName, field in fields:
            if not fieldName.islower() or fieldName.startswith('_') and fieldName not in ('_id', '_timestamp'):
                raise Exception('Field `%s` in Table `%s`: field names must be lowercase and must not start with `_`.' % (fieldName, name))
            field_ = field.__class__(name= fieldName, table= newClass) # recreate the field - to handle correctly inheritance of Tables
            field_._init(*field._initArgs, **field._initKwargs) # and initialize it
            setattr(newClass, fieldName, field_) # each class has its own field object. Inherited and parent tables do not share field attributes
                    
        return newClass

    def __getitem__(self, key):
        '''Get a Table Field by name - Table['field_name'].'''
        attr = getattr(self, key, None)
        if isinstance(attr, orm.fields.Field):
            return attr
        raise KeyError('Could not find field %s in table %s' % (key, self.__name__))

    def __iter__(self):
        '''Get Table fields.'''
        fields = []
        for attrName in self.__dict__:
            try:
                fields.append(self[attrName])
            except KeyError:
                pass 
        fields.sort(key= lambda field: field._orderNo) # sort by creation order - because __dict__ is unordered
        for field in fields:
            yield field

    def __str__(self):
        return getattr(self, '_name', '') or self.__name__.lower() 

    def delete(self, db, where):
        '''Delete records from this table which fall under the given condition.'''
        db.delete(self, where= where)
        db.commit()



class Model(metaclass= ModelMeta):
    '''Base class for all tables. Class attributes - the fields. 
    Instance attributes - the values for the corresponding table fields.'''
    
    _id = orm.fields.IdField() # this field is present in all tables
    _timestamp = orm.DateTimeField() # version of the record - datetime (with milliseconds) of the last update of this record
      
    _indexes = [] # each table subclass will have its own (metaclass will assure this)
    _ordering = [] # default order for select when not specified

    def __init__(self, db, *args, **kwargs):
        '''Create a model instance - a record.
        Pass arguments: tuples (Field, value) 
        and keyword arguments: fieldName= value.'''
        self._db = db #kwargs.pop('db')
        
        table = None
        for item in args:
            assert isinstance(item, (list, tuple)) and len(item) == 2, 'Pass tuples with 2 items: (field, value).'
            field, value = item
            assert isinstance(field, orm.Field), 'First item must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
            kwargs[field.name] = value

        for field in self.__class__: # make values for fields
            setattr(self, field.name, kwargs.pop(field.name, field.defaultValue))
            
        if kwargs:
            raise NameError('Got unknown field names: %s' % ', '.join(kwargs))

    def __getitem__(self, field):
        '''Get a Record Field value by key.
        key: either a Field instance or name of the field.'''
        table = self.__class__
        if isinstance(field, orm.Field):
            assert field.table is table, 'This field is from another table.'
            attrName = field.name
        elif isinstance(field, str):
            field = table[field]
            attrName = field.name
        else:
            raise TypeError('Pass either a Field or its name.')
        return getattr(self, attrName)
    
    @orm.metamethod
    def delete(self):
        '''Delete this record.'''
        db = self._db
        table = self.__class__
        db.delete(table, where= (table._id == self._id))
        db.commit()
        self._id = None
        
    @classmethod
    def getOne(cls, db, where):
        '''Get a single record which falls under the given condition.'''
        fields, rows = db.select(cls, where= where)
        if not rows: # not found
            raise orm.RecordNotFound
        if len(rows) == 1:
            return cls(db, *zip(fields, rows[0]))
        raise orm.TooManyRecords
        
        
    @classmethod
    def getOneById(cls, db, _id):
        '''Get one record by id.'''
        return cls.getOne(db, cls._id == _id)

    @classmethod
    def get(cls, db, where, orderBy= False, limit= False):
        '''Get records from this table which fall under the given condition.'''
        orderBy = orderBy or cls._ordering # use default table ordering if no ordering passed
        fields, rows = db.select(cls, where= where, orderBy= orderBy, limit= limit)
        for row in rows:
            yield cls(db, *zip(fields, row))

    def save(self):
        db = self._db
        table = self.__class__
        values = [] # list of tuples (Field, value)
        self._timestamp = DateTime.now()
        for field in table:
            value = self[field]
            values.append((field, value))
        if self._id: # existing record
            db.update(*values, where= (table._id == self._id))
            db.commit()
        else: # new record
            db.insert(*values)
            db.commit()
            self._id = db.lastInsertId()
        
        signals.post_delete.send(sender= self)

    def __str__(self):
        '''How the record is presented.'''
        return '%s(%s)' % (self.__class__.__name__, 
            ', '.join('%s= %r' % (field.name, getattr(self, field.name))
                       for field in self.__class__)) 

