try:
    from . import w_widgets_rc # load resources (icons, etc.)
except ImportError:
    print('Looks like resources are not compiled. Please run `compile_resources.py`.')