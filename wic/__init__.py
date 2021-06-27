"""
The framework for building apps similar to VBA.
"""
import importlib
import logging
import os
import sys

import peewee


logging.basicConfig(level=logging.INFO)

REQUIRED_PYTHON_VERSION = '3.9'  # tested with this version or later
if sys.version < REQUIRED_PYTHON_VERSION:
    raise SystemExit('Python %s or newer required (you are using: %s).'
                     % (REQUIRED_PYTHON_VERSION, sys.version))

try:  # load Qt resources (icons, etc.)
    from .widgets import widgets_rc
except ModuleNotFoundError as exc:
    raise SystemExit('Looks like the resources are not compiled:\n\n'
                     'If so, run `./wic/compile_resources.py`.')


class Bunch(dict):
    """Alex Martelli's recipe.
    """
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__ = self


MISSING = object()  # Custom None

database = None
database_proxy = peewee.DatabaseProxy()


from . import forms, menus, widgets, main_window, app


def get_object_by_path(object_path, package_path=None):
    """Given the path in form 'some.module.object' return the object.

    Args:
        object_path (str): path to an object
        package_path (str): if object_path is relative or only object name in it is given,
            package_path should be given.
    """
    module_path, sep, object_name = object_path.rpartition('.')
    if not sep:
        # '.' not present - only object name is given in the path
        assert package_path, "You've given the object name, but haven't specified the module in " \
                             "which to find it. " + object_path
        (object_name, module_path, package_path) = (object_path, package_path, None)
    module = importlib.import_module(module_path, package_path)
    return getattr(module, object_name)


wic_dir = os.path.dirname(os.path.abspath(__file__))

_app = None
