__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

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
    if hasattr(obj, '__iter__') and not isinstance(obj, ModelMeta):
        return list(obj)
    return [obj]


def metamethod(method):
    """Decorator for Model methods.
    When calling the method on an instance - calls its implemetation in the class.
    When calling the method on a class - calls the method in metaclass with the same name.
    """
    def wrapped(obj, *args, **kwargs):
        _method = method
        if isinstance(obj, type): # is a class
            _method = getattr(obj.__class__, method.__name__) # use metaclass's method instead
        return _method(obj, *args, **kwargs)
    return wrapped        


class LazyProperty():
    """The descriptor is designed to be used as a decorator, and will save the decorated function and its name.
    http://blog.pythonisito.com/2008/08/lazy-descriptors.html
    """
    def __init__(self, func):
        self._func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        """When the descriptor is accessed, it will calculate the value by calling the function and save the calculated value back to the object's dict.
        Saving back to the object's dict has the additional benefit of preventing the descriptor from being called the next time the property is accessed.
        """
        if instance is not None: # when the descriptor is accessed as an instance attribute
            result = instance.__dict__[self.__name__] = self._func(instance)
            return result
        else:
            return self # when the descriptor is accessed as a class attribute


class Nil():
    """Custom None"""


from .exceptions import *
from .adapters import *
from .fields import *
from .models import *


def connect(uri):
    """Search for suitable adapter by protocol
    """
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
