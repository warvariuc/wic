import inspect

import orm



#def prepareModels():
#    # fill Field's names where not defined
#    for tAttr in globals().copy().values():
#        if inspect.isclass(tAttr) and issubclass(tAttr, Table) and tAttr is not Table:
#            for fAttrName, fAttr in tAttr.__dict__.items():
#                if isinstance(fAttr, Field):
#                    if not fAttrName.islower():
#                        raise Exception('Field names must be lowercase. Field `{}` in Table `{}`'.format(fAttrName, tAttr.__name__))
#                    if fAttrName.startswith('_'):
#                        raise Exception('Field names can not start with `_`. Field `{}` in Table `{}`'.format(fAttrName, tAttr.__name__))
#                    if fAttr._name is not None:
#                        raise Exception('Duplicate Field `{}` in Table `{}`'.format(fAttrName, tAttr.__name__))
#                    if isinstance(fAttr, IdField) and fAttrName != 'id':
#                        fAttrName += '_id'
#                    fAttr._name = fAttrName
#                    fAttr._table = tAttr

class TableMetaClass(type):
    '''Metaclass for all tables.'''
    
    def __new__(cls, name, bases, attrs):
        newClass = type.__new__(cls, name, bases, attrs)
        
        if 'Table' in globals(): # only Table subclasses
            for attrName, attr in newClass.__dict__.items():
                if isinstance(attr, orm.Field):
                    if not attrName.islower():
                        raise Exception('Field names must be lowercase. Field `{}` in Table `{}`'.format(attrName, name))
                    if attrName.startswith('_'):
                        raise Exception('Field names can not start with `_`. Field `{}` in Table `{}`'.format(attrName, name))
                    if attr._name is not None:
                        raise Exception('Duplicate Field `{}` in Table `{}`'.format(attrName, name))
                    if isinstance(attr, orm.IdField) and attrName != 'id':
                        attrName += '_id'
                    attr._name = attrName
                    attr._table = newClass
        
        return newClass






class Table(metaclass=TableMetaClass):
    '''Base class for all tables.'''
    id = orm.IdField('id')
    #__indexes = DbIndex(Table.id, primary = True)

    def __init__(self, **kwargs):
        '''Initialize a new record in this table.'''
        self.dbAdapter = kwargs.pop('db', orm.defaultDbAdapter)
        
        # make field values 
        for fieldName, field in inspect.getmembers(self.__class__):
            if isinstance(field, orm.Field):
                fieldValue = field._cast(kwargs.pop(fieldName, field.defaultValue))
                setattr(self, fieldName, fieldValue)
            
    def delete(self):
        (self.__class__.id == self.id).delete(self.dbAdapter)
