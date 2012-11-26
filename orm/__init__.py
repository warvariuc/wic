__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import sys, os

python_required_version = '3.2'
if sys.version < python_required_version:
    sys.exit('Python %s or newer required (you are using: %s).' % (python_required_version, sys.version))


def _import(name, globals=None, locals=None, fromlist=None, level=-1):

    module = _base_import(name, globals, locals, fromlist, level)
    for attr in fromlist or []:
        sub_name = module.__name__ + '.' + attr
        sub_module = sys.modules.get(sub_name)
        if sub_module:
            # the key moment:
            # if subpackage is already being imported, even if not finished
            # inject its name into the parent package
            setattr(module, attr, sub_module)
#    print(module)
    return module

_base_import = __builtins__['__import__']
__builtins__['__import__'] = _import


import logging, inspect, importlib


logger = logging.getLogger('orm')
strm_out = logging.StreamHandler(sys.__stdout__)
strm_out.setFormatter(logging.Formatter())
logger.addHandler(strm_out)
logger.setLevel(logging.ERROR)  # logging level


def get_object_path(obj):
    """Having an object return path to its class in form of `path.to.module.ClassName`
    """
    if isinstance(obj, type):
        klass = obj
    else:
        klass = obj.__class__
    return klass.__module__ + '.' + klass.__name__


def get_object_by_path(object_path, package_path = None):
    """Given the path in form 'some.module.object' return the object.
    @param objectPath: path to an object
    @param packagePath: if objectPath is relative or only object name in it is given, packagePath should be given.
    """
    module_path, sep, object_name = object_path.rpartition('.')
    if not sep:  # '.' not present - only object name is given in the path
        assert package_path, "You've given the object name, but haven't specified the module in ' \
            'which i can find it. " + object_path
        object_name, module_path, package_path = object_path, package_path, None
    module = importlib.import_module(module_path, package_path)
    return getattr(module, object_name)


def is_model(obj):
    return isinstance(obj, models.ModelBase)


def listify(obj):
    """Assure that obj is a list."""
    if isinstance(obj, list):
        return obj
    elif hasattr(obj, '__iter__') and not isinstance(obj, str):
        return list(obj)
    return [obj]


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
        if instance is not None:  # when the descriptor is accessed as an instance attribute
            result = instance.__dict__[self.__name__] = self._func(instance)
            return result
        else:
            return self  # when the descriptor is accessed as a class attribute


# Custom None
Nil = object()


from .exceptions import *
from .adapters import *
from .models import *
from .model_options import ModelOptions
from .query_manager import QueryManager
from .indexes import *
from .fields import *


def connect(uri):
    """Search for suitable adapter by protocol in the given URI
    @param uri: database URI. Its form depends on the adapter, but generally is
        like 'protocol://username:password@host:port/db_name'
    @return: adapter instance, which handles the specified protocol
    """
    for AdapterClass in globals().values():
        if isinstance(AdapterClass, type) and issubclass(AdapterClass, GenericAdapter):
            uri_start = AdapterClass.protocol + '://'
            if uri.startswith(uri_start):
                db_adapter = AdapterClass(uri[len(uri_start):])
                return db_adapter
    raise AdapterNotFound('Could not find a suitable adapter for the URI `%s`' % uri)
