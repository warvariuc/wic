"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import sys, os

pythonRequiredVersion = '3.2'
if sys.version < pythonRequiredVersion:
    sys.exit('Python %s or newer required (you are using: %s).' % (pythonRequiredVersion, sys.version))


import logging, inspect, importlib

logger = logging.getLogger('orm')
strm_out = logging.StreamHandler(sys.__stdout__)
strm_out.setFormatter(logging.Formatter())
logger.addHandler(strm_out)
logger.setLevel(logging.DEBUG) # logging level


def getObjectByPath(objectPath, packagePath= None):
    """Given the path in form 'some.module.object' return the object.
    @param objectPath: path to an object
    @param packagePath: if objectPath is relative or only object name in it is given, packagePath should be given.
    """
    modulePath, sep, objectName = objectPath.rpartition('.')
    if not sep: # '.' not present - only object name is given in the path
        assert packagePath, "You've given the object name, but haven't specified the module in which i can find it. " + objectPath
        (objectName, modulePath, packagePath) = (objectPath, packagePath, None)
    module = importlib.import_module(modulePath, packagePath)
    return getattr(module, objectName)
    
def isModel(obj):
    return isinstance(obj, ModelMeta) # return isinstance(obj, type) and issubclass(obj, Model) # isinstance(res, type) == inspect.isclass(obj)

def listify(obj):
    """Assure that obj is a list."""
    if hasattr(obj, '__iter__'):
        return list(obj)
    return [obj]


def meta_method(method):
    """A decorator for Model methods. 
    When calling the method on an instance - calls its implemetation in the class.
    When calling the method on a class - calls the method in metaclass with the same name.
    """
    def wrapped(obj, *args, **kwargs):
        if isinstance(obj, type): # is a class
            method = getattr(obj.__class__, method.__name__) # use metaclass's method instead
        return method(obj, *args, **kwargs)
    return wrapped        



class Nil():
    """Custom None"""


from .exceptions import *
from .adapters import *
from .fields import *
from .models import *


def connect(uri):
    """Search for suitable adapter by protocol"""
    from . import adapters
    for AdapterClass in adapters.__dict__.values():
        if isinstance(AdapterClass, type) \
                and issubclass(AdapterClass, GenericAdapter) \
                and AdapterClass is not GenericAdapter: 
            uriStart = AdapterClass.protocol + '://'
            if uri.startswith(uriStart):
                dbAdapter = AdapterClass(uri[len(uriStart):])
                return dbAdapter
    raise AdapterNotFound('Could not find a suitable adapter for the URI ""%s' % uri)
