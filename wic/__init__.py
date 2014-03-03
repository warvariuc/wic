__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import sys
import os

REQUIRED_PYTHON_VERSION = '3.3.2'  # tested with this version or later
if sys.version < REQUIRED_PYTHON_VERSION:
    raise SystemExit('Python %s or newer required (you are using: %s).'
                     % (REQUIRED_PYTHON_VERSION, sys.version))

try:  # load Qt resources (icons, etc.)
    from .widgets import w_widgets_rc
except ImportError as exc:
    raise SystemExit('Looks like the resources are not compiled:\n%s\n\n'
                     'If so, run `wic/compile_resources.py`.' % exc)

try:  # monkeypatch: use cdecimal instead of decimal, if present - it is faster
    import cdecimal
    sys.modules['decimal'] = cdecimal
except ImportError:
    pass


class Bunch(dict):
    """Alex Martelli's recipe"""
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__ = self


from . import forms, menus, widgets

wicDir = os.path.dirname(os.path.abspath(__file__))

app = None

from orm import getObjectByPath


#import errno
#
#def pid_exists(pid):
#    """Verify if process with given pid is running (on this machine)."""
#    try:
#        os.kill(pid, 0)
#    except OSError as exc:
#        return exc.errno == errno.EPERM
#    else:
#        return True
