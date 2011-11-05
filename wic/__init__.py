import sys, os

if sys.hexversion < 0x03010000:
    sys.exit("Python 3.1 or newer required.")

appDir = os.path.dirname(os.path.abspath(__file__))

from .widgets import w_widgets_rc # load resources (icons, etc.)
