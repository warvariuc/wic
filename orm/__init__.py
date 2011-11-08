'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''
import sys, os

if sys.hexversion < 0x03010000:
    raise SystemExit('At least Python 3.1 needed. Exiting.')


import logging, inspect

logger = logging.getLogger("wic.orm")

_fieldsCount = 0 # will be used to track the original definition order of the fields 
_tablesCount = 0 

def getObjectByPath(path, defaultModule):
    '''Given the path in form 'some.module.object' return the object. 
    If '.' is not present in path return object from defaultModule with that name.'''
    moduleName, sep, className = str(path).rpartition('.')
    if sep: # '.' is present 
        module = __import__(moduleName, fromlist= [className])
        return getattr(module, className)            
    return getattr(sys.modules[defaultModule], path) 
    
def isModel(obj):
    return isinstance(obj, type) and issubclass(obj, Model) # isinstance(res, type) == inspect.isclass(obj)

def listify(obj):
    '''Assure that obj is an iterable.'''
    if not hasattr(obj, '__iter__'):
        obj = [obj]
    return list(obj)

class metamethod():
    '''A descriptor you can use to decorate a method. 
    Then calling that method as instance method - calls its implemetation in the class.
    Then calling that method as class method - calls its implemetation in the metaclass.'''
    def __init__(self, method):
        self.method = method

    def __get__(self, obj, objtype):
        if obj is None:
            obj = objtype
        def wrapped(*args, **kwargs):
            method = self.method
            if isinstance(obj, type): # is a class
                method = getattr(obj.__class__, method.__name__) # use metaclass's method instead
            return method(obj, *args, **kwargs)
        return wrapped        


from .exceptions import *

from .fields import Expression, Field, IdField, IntegerField, StringField, DecimalFieldI,\
                    RecordIdField, AnyRecordField, COUNT, MAX, MIN
from .models import Model, Index, Join, LeftJoin
from .adapters import SqliteAdapter, MysqlAdapter, GenericAdapter

#defaultAdapter = _Adapter(connect=False)

def connect(uri, adapters):
    '''Search for suitable adapter by protocol'''
    for dbType, dbAdapterClass in adapters.items(): 
        uriStart = dbType + '://'
        if uri.startswith(uriStart):
            dbAdapter = dbAdapterClass(uri[len(uriStart):])
            return dbAdapter

