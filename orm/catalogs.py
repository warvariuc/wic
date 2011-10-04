import inspect
import orm


class CatalogMeta(type):
    '''Metaclass for all tables.'''
    
    def __new__(cls, name, bases, attrs):
        newClass = type.__new__(cls, name, bases, attrs)
        
        if 'Catalog' in globals(): # only Table subclasses. if Table is not defined - __new__ is called for it
            if not hasattr(newClass, '_tableId'):
                raise Exception('Table ID not set in {}!'.format(newClass))
            newClass._indexes = {}
            for fieldName, field in newClass.getFields().items():
                if not fieldName.islower() or fieldName.startswith('_'):
                    raise Exception('Field `{}` in Table `{}`: field names must be lowercase and must not start with `_`.'.format(fieldName, name))
                field_ = field.__class__() # recreate the field - to handle correctly inheritance
                field_.name = fieldName
                field_.table = newClass
                field_._init(*field._initArgs, **field._initKwargs) # and initialize it
                setattr(newClass, fieldName, field_) # each class has its own field object. Inherited and parent tables do not share field attributes
        return newClass


class Catalog(metaclass=CatalogMeta):
    '''Base class for all tables. Class attributes - the fields. 
    Instance attributes with the same names - the values for the corresponding fields.'''
    id = orm.IdField() # this field is present in all tables

    def __init__(self, **kwargs):
        '''Initialize a new item in this table.'''
        self.adapter = kwargs.pop('db', orm.defaultAdapter)
        
        # make values for fields 
        for fieldName, field in inspect.getmembers(self.__class__):
            if isinstance(field, orm.fields.Field):
                fieldValue = field._cast(kwargs.pop(fieldName, field.defaultValue))
                setattr(self, fieldName, fieldValue)
    
    @classmethod
    def getFields(cls):
        return {fieldName: field for fieldName, field in inspect.getmembers(cls) 
                if isinstance(field, orm.fields.Field)}
            
    def delete(self):
        (self.__class__.id == self.id).delete(self.adapter)
