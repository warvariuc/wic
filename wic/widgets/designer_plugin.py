"""
This file contains all custom widget plugins for Wic platform.

Author: Victor Varvariuc <victor.varvariuc@gmail.com>
"""

import os, sys
import importlib

from PyQt4 import QtGui, QtDesigner


print('Python version used:', sys.version)
curDir = os.path.dirname(__file__)
wicDir = os.path.abspath(os.path.join(curDir, '..', '..'))

if wicDir not in sys.path:
    sys.path.append(wicDir)



class WDateEditPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    """Designer plugin for WDateEdit. 
    Also serves as base class for other custom widget plugins:"""

    _module = 'wic.widgets.w_date_edit' # path to the widget's module
    _class = 'WDateEdit' # name of the widget class
    _icon = ':/icons/fugue/calendar-blue.png' # path to the icon in the resources

    def __init__(self, parent = None):
        super().__init__(parent)
        self.initialized = False

    def initialize(self, formEditor):
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def isContainer(self):
        return False

    def icon(self):
        return QtGui.QIcon(self._icon)

    def domXml(self):
        return '<widget class="%s" name="%s">\n</widget>\n' % (self._class, self.name())

    def group(self):
        return 'wic'

    def includeFile(self):
        return self._module

    def name(self):
        return self._class

    def toolTip(self):
        return ''

    def whatsThis(self):
        return ''

    def createWidget(self, parent):
        module = importlib.import_module(self._module)
        Klass = getattr(module, self._class)
        return Klass(parent)



class WDecimalEditPlugin(WDateEditPlugin):

    _module = 'wic.widgets.w_decimal_edit'
    _class = 'WDecimalEdit'
    _icon = ':/icons/calculator.png'



class WCatalogItemWidgetPlugin(WDateEditPlugin):

    _module = 'wic.widgets.w_catalog_item_widget'
    _class = 'WCatalogItemWidget'
    _icon = ':/icons/fugue/card-address.png'




if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])
    plugin = WDateEditPlugin()
    print(plugin)
    print(plugin.includeFile())
    print(plugin.name())
    print(plugin.group())
    widget = plugin.createWidget(None)
    widget.show()
    app.exec()
