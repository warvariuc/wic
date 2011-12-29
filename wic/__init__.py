"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import sys, os

pythonRequiredVersion = '3.2'
if sys.version < pythonRequiredVersion:
    sys.exit('Python %s or newer required (you are using: %s).' % (pythonRequiredVersion, sys.version))

try:
    from wic.widgets import w_widgets_rc # load resources (icons, etc.)
except ImportError:
    sys.exit('Looks like resources are not compiled. Please run `compile_resources.py`.')

try: # monkeypatch: use cdecimal instead of decimal, if present - it is faster
    import cdecimal
    sys.modules['decimal'] = cdecimal
except ImportError:
    pass



class Bunch(): # Alex Martelli's recipe
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


wicDir = os.path.dirname(os.path.abspath(__file__))

app = None

import orm
getObjectByPath = orm.getObjectByPath

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