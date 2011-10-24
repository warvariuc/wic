'''Author: Victor Varvariuc <victor.varvariuc@gmail.com'''

import logging, sys, inspect

logger = logging.getLogger("wic.orm")

_fieldsCount = 0 # will be used to track the original definition order of the fields 
_tablesCount = 0 

def getObjectByPath(path, defaultModule):
    '''Given the path in form 'some.module.object' return the object. 
    If '.' is not present in path return object from defaultModule with that name.'''
    moduleName, sep, className = str(path).rpartition('.')
    if sep: # '.' is present 
        module = __import__(moduleName, fromlist=[className])
        return getattr(module, className)            
    return getattr(sys.modules[defaultModule], path) 
    
def isTable(obj):
    return inspect.isclass(obj) and issubclass(obj, Table)

def listify(obj):
    '''Assure that obj is an iterable.'''
    if not hasattr(obj, '__iter__'):
        obj = [obj]
    return obj


from orm.fields import Expression, Field, IdField, IntegerField, StringField, DecimalFieldI, RecordIdField, AnyRecordField
from orm.tables import Table, Record, Index
from orm.adapters import SqliteAdapter, MysqlAdapter, Adapter

#defaultAdapter = _Adapter(connect=False)

def connect(uri, adapters):
    '''Search for suitable adapter by protocol'''
    for dbType, dbAdapterClass in adapters.items(): 
        uriStart = dbType + '://'
        if uri.startswith(uriStart):
            dbAdapter = dbAdapterClass(uri[len(uriStart):])
            return dbAdapter



