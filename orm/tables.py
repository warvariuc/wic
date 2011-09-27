import inspect
import orm


class TableMetaClass(type):
    '''Metaclass for all tables.'''
    
    def __new__(cls, name, bases, attrs):
        newClass = type.__new__(cls, name, bases, attrs)
        
        if 'Table' in globals(): # only Table subclasses. if Table is not defined - __new__ is called for it
            for attrName, attr in newClass.__dict__.items():
                if isinstance(attr, orm.fields.Field):
                    if not attrName.islower():
                        raise Exception('Field names must be lowercase. Field `{}` in Table `{}`'.format(attrName, name))
                    if attrName.startswith('_'):
                        raise Exception('Field names can not start with `_`. Field `{}` in Table `{}`'.format(attrName, name))
                    if attr._name is not None:
                        raise Exception('Duplicate Field `{}` in Table `{}`'.format(attrName, name))
                    if isinstance(attr, orm.ReferenceField):
                        attrName += '_id'
                    attr._name = attrName
                    attr._table = newClass
        
        return newClass



class Table(metaclass=TableMetaClass):
    '''Base class for all tables. Class attributes - the fields. 
    Instance attributes with the same names - the values for the corresponding fields.'''
    id = orm.IdField('id')
    #__indexes = DbIndex(Table.id, primary = True)

    def __init__(self, **kwargs):
        '''Initialize a new record in this table.'''
        self.dbAdapter = kwargs.pop('db', orm.defaultDbAdapter)
        
        # make values for fields 
        for fieldName, field in inspect.getmembers(self.__class__):
            if isinstance(field, orm.fields.Field):
                fieldValue = field._cast(kwargs.pop(fieldName, field.defaultValue))
                setattr(self, fieldName, fieldValue)
            
    def delete(self):
        (self.__class__.id == self.id).delete(self.dbAdapter)
