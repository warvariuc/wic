import os, sys
print('Python', sys.version)
curDir = os.path.dirname(os.path.abspath(__file__))
wicDir = os.path.abspath(os.path.join(curDir, '..', '..'))

if wicDir not in sys.path:
    sys.path.insert(0, wicDir)
    

# Designer plugin for:
widgetClassName = 'WDecimalEdit'
widgetModuleName = 'wic.widgets.w_decimal_edit'
widgetIconName = ':/icons/calculator.png'

from PyQt4 import QtGui, QtDesigner
from wic.widgets import w_decimal_edit as widgetModule

class DesignerPlugin(QtDesigner.QPyDesignerCustomWidgetPlugin):
    def __init__(self, parent= None):
        super().__init__(parent)
        self.initialized = False

    def initialize(self, formEditor):
        self.initialized = True

    def isInitialized(self):
        return self.initialized

    def isContainer(self):
        return False

    def icon(self):
        return QtGui.QIcon(widgetIconName)

    def domXml(self):
        return '<widget class="%s" name="%s">\n</widget>\n' % (widgetClassName, self.name())
    
    def group(self):
        return 'wic'
              
    def includeFile(self):
        return widgetModuleName

    def name(self):
        return widgetClassName

    def toolTip(self):
        return ''

    def whatsThis(self):
        return ''

    def createWidget(self, parent):
        return getattr(widgetModule, widgetClassName)(parent)


if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])
    w = DesignerPlugin()
    print(w.domXml())
    print(w.includeFile())
    print(w.name())
    print(w.group())
    w1 = w.createWidget(None)
    w1.show()
    app.exec()