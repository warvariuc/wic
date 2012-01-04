"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import inspect
from datetime import datetime as DateTime
import orm
from orm import signals


class Index():
    """Defines a DB table index.
    type: index, unique, fulltext, spatial
    sort: asc, desc
    method: btree, hash, gist, and gin"""
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
    """Object holding parameters for a join."""
    def __init__(self, model, on, type= ''):
        assert orm.isModel(model), 'Pass a model class.'
        assert isinstance(on, orm.fields.Expression), 'WHERE should be an Expression.'
        self.model = model # table to join
        self.on = on # expression defining join condition
        self.type = type # join type. if empty - INNER JOIN


class LeftJoin(Join):
    """Left join parameters."""
    def __init__(self, table, on):
        super().__init__(table, on, 'left')
        


class ModelMeta(type):
    """Metaclass for all tables (models).
    It gives names to all fields and makes instances for fields for each of the models. 
    It has some class methods for models."""
    
    def __new__(cls, name, bases, attrs):
        NewClass = type.__new__(cls, name, bases, attrs)
        
        try: # we need only Model subclasses
            Model
        except NameError: # if Model is not defined: __new__ is called for Model itself
            return NewClass # return wihout any processing
        
        NewClass._indexes = list(NewClass._indexes) # assure each class has its own attribute
        for index in NewClass._indexes :
            assert isinstance(index, Index), 'Found a non Index in the _indexes.'
            
        fields = []
        for fieldName, field in inspect.getmembers(NewClass):
            if isinstance(field, orm.fields.Field):
                fields.append((fieldName, field)) 
                    
        fields.sort(key= lambda f: f[1]._orderNo) # sort by definition order (as __dict__ is unsorted) - for field recreation order
        for fieldName, field in fields:
            if not fieldName.islower() or fieldName.startswith('_'):
                raise Exception('Field `%s` in Table `%s`: field names must be lowercase and must not start with `_`.' % (fieldName, name))
            field_ = field.__class__(name= fieldName, table= NewClass, label= field.label) # recreate the field - to handle correctly inheritance of Tables
            try:
                field_._init(*field._initArgs, **field._initKwargs) # and initialize it
            except Exception:
                print('Failed to init a field:', fieldName, field._initArgs, field._initKwargs)
                raise
            setattr(NewClass, fieldName, field_) # each class has its own field object. Inherited and parent tables do not share field attributes
                    
        return NewClass

    def __getitem__(self, key):
        """Get a Table Field by name - Table['field_name']."""
        attr = getattr(self, key, None)
        if isinstance(attr, orm.fields.Field):
            return attr
        raise KeyError('Could not find field %s in table %s' % (key, self.__name__))

    def __iter__(self):
        """Get Table fields."""
        fields = []
        for attrName in self.__dict__:
            try:
                fields.append(self[attrName])
            except KeyError:
                pass 
        fields.sort(key= lambda field: field._orderNo) # sort by creation order - because __dict__ is unordered
        for field in fields:
            yield field

    def __len__(self):
        return len(list(self.__iter__()))
    
    def __str__(self):
        return getattr(self, '_name', '') or self.__name__.lower() 

    def delete(self, db, where):
        """Delete records from this table which fall under the given condition."""
        db.delete(self, where= where)
        db.commit()



class Model(metaclass= ModelMeta):
    """Base class for all tables. Class attributes - the fields. 
    Instance attributes - the values for the corresponding table fields."""
    
    id = orm.fields.IdField() # this field is present in all tables
    timestamp = orm.DateTimeField() # version of the record - datetime (with milliseconds) of the last update of this record
      
    _indexes = [] # each table subclass will have its own (metaclass will assure this)
    _ordering = [] # default order for select when not specified

    def __init__(self, db, *args, **kwargs):
        """Create a model instance - a record.
        Pass arguments: tuples (Field, value) 
        and keyword arguments: fieldName= value."""
        self._db = db
        
        table = None
        for arg in args:
            assert hasattr(arg, '__iter__') and len(arg) == 2, 'Pass tuples with 2 items: (field, value).'
            field, value = arg
            assert isinstance(field, orm.Field), 'First arg must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
            kwargs[field.name] = value

        for field in self.__class__: # make values for fields
            setattr(self, field.name, kwargs.pop(field.name, field.defaultValue))
            
        if kwargs:
            raise NameError('Got unknown field names: %s' % ', '.join(kwargs))

    def __getitem__(self, field):
        """Get a Record Field value by key.
        key: either a Field instance or name of the field."""
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
        """Delete this record."""
        db = self._db
        table = self.__class__
        signals.post_delete.send(sender= table, record= self)
        db.delete(table, where= (table.id == self.id))
        db.commit()
        self.id = None
        signals.post_delete.send(sender= table, record= self)
        
    @classmethod
    def getOne(cls, db, where):
        """Get a single record which falls under the given condition."""
        records = list(cls.get(db, where, limit= (0, 2)))
        if not records: # not found
            raise orm.RecordNotFound(where._render(db))
        if len(records) == 1:
            return records[0]
        raise orm.TooManyRecords
        
        
    @classmethod
    def getOneById(cls, db, id):
        """Get one record by id."""
        return cls.getOne(db, cls.id == id)

    @classmethod
    def get(cls, db, where, orderBy= False, limit= False):
        """Get records from this table which fall under the given condition."""
        orderBy = orderBy or cls._ordering # use default table ordering if no ordering passed
        rows = db.select(cls, where= where, orderBy= orderBy, limit= limit)
        for row in rows:
            yield cls(db, *zip(rows.fields, row))

    def save(self):
        db = self._db
        table = self.__class__
        values = [] # list of tuples (Field, value)
        self.timestamp = DateTime.now()
        for field in table:
            value = self[field]
            values.append((field, value))
        isNew = not self.id
        signals.pre_save.send(sender= table, record= self)
        if isNew: # new record
            db.insert(*values)
            self.id = db.lastInsertId()
        else: # existing record
            rowsCount = db.update(*values, where= (table.id == self.id))
            if not rowsCount:
                raise orm.exceptions.SaveError('Looks like the record was deleted: table=`%s`, id=%s' % (table, self.id))
        db.commit()
        
        signals.post_save.send(sender= table, record= self, isNnew= isNew)

    def __str__(self):
        """How the record is presented."""
        return '%s(%s)' % (self.__class__.__name__, 
            ', '.join("%s= '%s'" % (field.name, getattr(self, field.name))
                       for field in self.__class__)) 

    @classmethod
    def count(cls, db, where= None):
        """Request number of records in this table."""
        count = orm.COUNT(where or cls) # COUNT expression
        return db.select(count).value(0, count)
