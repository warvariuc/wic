"""Author: Victor Varvariuc <victor.varvariuc@gmail.com>"""

import inspect
from datetime import datetime as DateTime, date as Date
from decimal import Decimal
from collections import OrderedDict
import orm
from orm import signals, logger, exceptions



class Join():
    """Object holding parameters for a join.
    """
    def __init__(self, model, on, type = ''):
        assert isinstance(model, orm.ModelMeta), 'Pass a model class.'
        assert isinstance(on, orm.Expression), 'WHERE should be an Expression.'
        self.model = model # table to join
        self.on = on # expression defining join condition
        self.type = type # join type. if empty - INNER JOIN


class LeftJoin(Join):
    """Left join parameters.
    """
    def __init__(self, table, on):
        super().__init__(table, on, 'left')



class ModelMeta(type):
    """Metaclass for all tables (models).
    It gives names to all fields and makes instances for fields for each of the models. 
    It has some class methods for models.
    """
    def __new__(cls, name, bases, attrs):
        NewModel = type.__new__(cls, name, bases, attrs)

        NewModel._name = NewModel.__dict__.get('_name', name.lower()) # db table name

        if NewModel._name is None: # we need only Model subclasses; if db table name is None - __new__ is called for Model itself
            return NewModel # return without any processing

        logger.debug('Finishing initialization of model `%s`' % NewModel)

        NewModel._indexes = list(NewModel._indexes) # assure each class has its own attribute, because by default _indexes is inherited from the parent class

        attrs = OrderedDict(inspect.getmembers(NewModel))
        fields = []
        for fieldName, field in attrs.items():
            if isinstance(field, orm.fields.Field):
                fields.append((fieldName, field))

        fields = OrderedDict(sorted(fields, key = lambda f: f[1]._id)) # sort by definition order (as __dict__ is unsorted) - for field recreation order

        for fieldName, field in fields.items():
            if not fieldName.islower() or fieldName.startswith('_'):
                raise orm.ModelError('Field `%s` in model `%s`: field names must be lowercase and must not start with `_`.' % (fieldName, name))

            newField = field.__class__(name = fieldName, table = NewModel, label = field.label) # recreate the field - to handle correctly inheritance of Tables
            try:
                newField._init_(*field._initArgs, **field._initKwargs) # and initialize it
            except Exception:
                print('Failed to init a field:', fieldName, field._initArgs, field._initKwargs)
                raise
            setattr(NewModel, fieldName, newField) # each class has its own field object. Inherited and parent tables do not share field attributes

        indexesDict = OrderedDict() # to filter duplicate indexes by index name
        for index in NewModel._indexes:
            if index.table is not NewModel: # inherited index
                if not isinstance(index, orm.Index):
                    raise orm.ModelError('Found a non Index in the _indexes.')
                if index.table is not NewModel: # index was inherited from parent model - recreate it with fields from new model
                    indexFields = [orm.IndexField(NewModel[indexField.field.name], indexField.sortOrder, indexField.prefixLength)
                                   for indexField in index.indexFields] # replace fields by name with fields from new model
                    index = orm.Index(indexFields, index.type, index.name, index.method, **index.other)
                for indexField in index.indexFields:
                    if issubclass(NewModel, indexField.field.table):
                        indexField.field = NewModel[indexField.field.name] # to assure that field from this model, and from parent, is used
                    else:
                        raise orm.ModelError('Field `%s` in index is not from model `%s`.' % (indexField.field, NewModel))
            indexesDict[index.name] = index
        NewModel._indexes = indexesDict.values()
        NewModel._ordering = list()
        NewModel._checkedDbs = set()

        return NewModel

    def __getitem__(self, key):
        """Get a Table Field by name - Table['field_name'].
        """
        attr = getattr(self, key, None)
        if isinstance(attr, orm.fields.Field):
            return attr
        raise KeyError('Could not find field %s in table %s' % (key, self.__class__))

    def __iter__(self):
        """Get Table fields.
        """
        fields = []
        for attrName in self.__dict__:
            try: # there maybe non Field attributes as well
                fields.append(self[attrName])
            except KeyError:
                pass
        fields.sort(key = lambda field: field._id) # sort by creation order - because __dict__ is unordered
        for field in fields:
            yield field

    def __len__(self):
        return len(list(self.__iter__()))

    def __str__(self):
        return self._name

    def delete(self, db, where):
        """Delete records in this table which fall under the given condition.
        """
        self.checkTable(db)
        db.delete(self, where = where)
        db.commit()



class Model(metaclass = ModelMeta):
    """Base class for all tables. Class attributes - the fields. 
    Instance attributes - the values for the corresponding table fields.
    """
    _indexes = [] # list of db table indexes (Index instances); each model will have its own copy - i.e. it's not inherited by subclasses (metaclass assures this)
    _ordering = [] # default order for select when not specified - overriden
    _checkedDbs = set() # ids of database adapters this model was successfully checked against

    _name = None # db table name

    # default fields
    id = orm.IdField() # row id. This field is present in all tables
    timestamp = orm.DateTimeField() # version of the record - datetime (with milliseconds) of the last update of this record

    def __init__(self, db, *args, **kwargs):
        """Create a model instance - a record.
        @param db: db adapter in which to save the table record or from which it was fetched
        @param *args: tuples (Field or field_name, value) 
        @param **kwargs: {fieldName: fieldValue}
        """
        self._db = db

        table = None
        for arg in args:
            assert hasattr(arg, '__iter__') and len(arg) == 2, 'Pass tuples with 2 items: (field, value).'
            field, value = arg
            if isinstance(field, str):
                field = self.__class__[field]
            assert isinstance(field, orm.Field), 'First arg must be a Field.'
            _table = field.table
            table = table or _table
            assert table is _table, 'Pass fields from the same table'
            kwargs[field.name] = value

        for field in self.__class__: # make values for fields
            setattr(self, field.name, kwargs.pop(field.name, field.default))

        if kwargs:
            raise NameError('Got unknown field names: %s' % ', '.join(kwargs))

    def __getitem__(self, field):
        """Get a Record Field value by key.
        key: either a Field instance or name of the field.
        """
        model = self.__class__
        if isinstance(field, orm.Field):
            assert field.table is model, 'This field is from another model.'
            attrName = field.name
        elif isinstance(field, str):
            field = model[field]
            attrName = field.name
        else:
            raise TypeError('Pass either a Field or its name.')
        return getattr(self, attrName)

    @orm.metamethod
    def delete(self):
        """Delete this record.
        """
        db = self._db
        self.checkTable(db)
        model = self.__class__
        signals.post_delete.send(sender = model, record = self)
        db.delete(model, where = (model.id == self.id))
        db.commit()
        self.id = None
        signals.post_delete.send(sender = model, record = self)

    @classmethod
    def getOne(cls, db, where = None, id = None, select_related = False):
        """Get a single record which falls under the given condition.
        @param db: db adapter to use to getting the record
        @param where: expression to use for filter
        @param id: id of the record, if you want to fetch one record by its id
        """
        cls.checkTable(db)

        if id:
            where = (cls.id == id)

        records = list(cls.get(db, where, limit = 2, select_related = select_related))
        if not records: # not found
            raise orm.RecordNotFound(db.render(where))
        if len(records) == 1:
            return records[0]
        raise orm.TooManyRecords

    @classmethod
    def get(cls, db, where, orderby = False, limit = False, select_related = False):
        """Get records from this table which fall under the given condition.
        @param db: adapter to use
        @param where: condition to filter
        @param order: list of field to sort by
        @param limit: tuple (from, to)
        @param select_related: whether to retrieve objects related by foreign keys in the same query
        """
        logger.debug('Model.get(%s, db= %s, where= %s, limit= %s)' % (cls, db, where, limit))
        cls.checkTable(db)
        orderby = orderby or cls._ordering # use default table ordering if no ordering passed
        fields = list(cls)
        from_ = [cls]
        recordFields = []
        if select_related:
            for i, field in enumerate(cls):
                if isinstance(field, orm.RecordField):
                    recordFields.append((i, field))
                    fields.extend(field.referTable)
                    from_.append(orm.LeftJoin(field.referTable, field == field.referTable.id))
        #print(db._select(*fields, from_ = from_, where = where, orderby = orderby, limit = limit))
        rows = db.select(*fields, from_ = from_, where = where, orderby = orderby, limit = limit)
        for row in rows:
            record = cls(db, *zip(cls, row))
            if select_related:
                fieldOffset = len(cls)
                for i, recordField in recordFields:
                    referTable = recordField.referTable
                    if row[i] is None: 
                        referRecord = None
                    else:
                        # if referRecord.id is None: # missing record !!! integrity error
                        referRecord = referTable(db, *zip(referTable, row[fieldOffset:]))
                    setattr(record, recordField.name, referRecord)
                    fieldOffset += len(referTable)
            yield record

    def save(self):
        db = self._db
        self.checkTable(db)
        model = self.__class__
        self.timestamp = DateTime.now()
        values = [] # list of tuples (Field, value)
        for field in model:
            value = self[field]
            values.append(field(value))

        signals.pre_save.send(sender = model, record = self)

        isNew = not self.id
        if isNew: # new record
            db.insert(*values)
            self.id = db.lastInsertId()
        else: # existing record
            rowsCount = db.update(*values, where = (model.id == self.id))
            if not rowsCount:
                raise orm.exceptions.SaveError('Looks like the record was deleted: table=`%s`, id=%s' % (model, self.id))
        db.commit()

        signals.post_save.send(sender = model, record = self, isNew = isNew)

    def __str__(self):
        """Human readable presentation of the record.
        """
        values = []
        for field in self.__class__:
            value = getattr(self, field.name)
            if isinstance(value, (Date, DateTime, Decimal)):
                value = str(value)
            values.append("%s= %r" % (field.name, value))
        return '%s(%s)' % (self.__class__.__name__, ', '.join(values))

    @classmethod
    def COUNT(cls, where = None):
        """Get COUNT expression for this table.
        @param where: WHERE expression
        """
        return orm.COUNT(where or cls) # COUNT expression

    @classmethod
    def getCount(cls, db, where = None):
        """Request number of records in this table.
        """
        cls.checkTable(db)
        count = cls.COUNT(where)
        count = db.select(count, from_ = cls).value(0, count)
        logger.debug('Model.getCount(%s, db= %s, where= %s) = %s' % (cls, db, where, count))
        return count

    @classmethod
    def _handleTableMissing(cls, db):
        """Default implementation of situation when upon checking
        there was not found the table corresponding to this model in the db.
        """
        raise exceptions.TableMissing(db, cls)

    @classmethod
    def checkTable(cls, db):
        """Check if corresponding table for this model exists in the db and has all necessary columns.
        Add checkTable call in very model method that uses a db.
        """
        assert isinstance(db, orm.GenericAdapter), 'Need a database adapter'
        if db.uri in cls._checkedDbs: # this db was already checked 
            return
        logger.debug('Model.checkTable: checking db table %s' % cls)
        tableName = cls._name
        if tableName not in db.getTables():
            cls._handleTableMissing(db)
#        import pprint
        modelColumns = {field.column.name: field.column for field in cls}
        dbColumns = db.getColumns(tableName)
#        logger.debug(pprint.pformat(list(column.str() for column in dbColumns.values())))
#        logger.debug(pprint.pformat(list(column.str() for column in modelColumns.values())))
        for columnName, column in modelColumns.items():
            dbColumn = dbColumns.pop(columnName, None)
            if not dbColumn: # model column is not found in the db
                print('Column in the db not found: %s' % column.str())
        logger.debug('CREATE TABLE query:\n%s' % db.getCreateTableQuery(cls))
        cls._checkedDbs.add(db.uri)
