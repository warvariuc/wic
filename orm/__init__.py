"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import sys, os

pythonRequiredVersion = '3.2'
if sys.version < pythonRequiredVersion:
    sys.exit('Python %s or newer required (you are using: %s).' % (pythonRequiredVersion, sys.version))


import logging, inspect, importlib

logger = logging.getLogger('wic.orm')

_fieldsCount = 0 # will be used to track the original definition order of the fields 

def getObjectByPath(objectPath, packagePath= None):
    """Given the path in form 'some.module.object' return the object.
    If path is relative or only object name in the path is given, modulePath should be given."""
    modulePath, sep, objectName = str(objectPath).rpartition('.')
    if not sep: # '.' not present - only object name is given in the path
        assert packagePath, "You've given the object name, but haven't specified the module in which i can find it. " + objectPath
        objectName = objectPath
        objectPath = packagePath
    module = importlib.import_module(modulePath, packagePath)
    return getattr(module, objectName)
    
def isModel(obj):
    return isinstance(obj, type) and issubclass(obj, Model) # isinstance(res, type) == inspect.isclass(obj)

def listify(obj):
    """Assure that obj is an iterable."""
    if hasattr(obj, '__iter__'):
        return list(obj)
    return [obj]

class metamethod():
    """A descriptor you can use to decorate a method. 
    When calling that method as instance method - calls its implemetation in the class.
    When calling that method as class method - calls its implemetation in the metaclass."""
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
from .fields import Expression, Field, IdField, IntegerField, CharField, TextField, DecimalField, DateField, \
                    DateTimeField, BooleanField, RecordIdField, COUNT, MAX, MIN, UPPER, LOWER
from .models import Model, Index, Join, LeftJoin
from .adapters import SqliteAdapter, MysqlAdapter, GenericAdapter

#defaultAdapter = _Adapter(connect=False)

def connect(uri, adapters):
    """Search for suitable adapter by protocol"""
    for dbType, dbAdapterClass in adapters.items(): 
        uriStart = dbType + '://'
        if uri.startswith(uriStart):
            dbAdapter = dbAdapterClass(uri[len(uriStart):])
            return dbAdapter
    raise Exception('Could not find a suitable adapter for the URI ""%s' % uri)
