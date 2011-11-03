import sys

if sys.hexversion < 0x03010000:
    sys.exit("Python 3.1 or newer required.")

from .widgets import w_widgets_rc # load resources (icons, etc.)
