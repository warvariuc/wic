import os, sys
from PyQt4 import QtGui, QtCore, uic
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit


class WForm(QtGui.QDialog):
    '''QObject allows having signals - f.e. about some value selected.'''
    uiFilePath = 'form.ui'
    
    def __init__(self, parentWidget):
        super().__init__(parentWidget)
        
        moduleName = self.__class__.__module__
        module = sys.modules[moduleName]
        moduleDir = os.path.dirname(os.path.abspath(module.__file__)) 
        uiFilePath = os.path.join(moduleDir, self.uiFilePath)
            
        uic.loadUi(uiFilePath, self)
        #self.widgets = WFormWidgetHooker(self.form) # helper for the form
        self.on_open() # предопределенная процедура

    def closeEvent(self, event):
        if self.on_close() == False: # вызов предопределенной процедуры
            event.ignore()
            return
        #self.reject()

    def on_close(self):
        pass

    def on_open(self):
        pass
    
    def widgetValidate(self):
        pass
