import logging, sys

logger = logging.getLogger("wic.orm")

_fieldsCount = 0 # will be used to track the original definition order of the fields 

def getObjectByPath(path, defaultModule):
    '''Given the path in form 'some.module.object' return the object. 
    If '.' is not present in path return object from defaultModule with that name.'''
    moduleName, sep, className = str(path).rpartition('.')
    if sep: # '.' is present 
        module = __import__(moduleName, fromlist=[className])
        return getattr(module, className)            
    return getattr(sys.modules[defaultModule], path) 
    

class class_or_instance_method():
    '''If you decorate a method with this - it will pass as the first argument instance or class.'''
    def __init__(self, method):
        self.method = method
    
    def __get__(self, obj, objType):
        if obj is None:
            obj = objType
        def wrapped(*args, **kwargs):
            return self.method(obj, *args, **kwargs)
        return wrapped        


from orm.fields import IdField, StringField, DecimalFieldI, RecordIdField, AnyRecordIdField
from orm.tables import Table, Record, Index
from orm.adapters import SqliteAdapter, MysqlAdapter, Adapter as _Adapter

defaultAdapter = _Adapter()


