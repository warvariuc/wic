import os, sys
from PyQt4 import QtGui, QtCore, uic
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit


class WForm(QtGui.QDialog):
    '''QObject allows having signals - f.e. about some value selected.'''
    uiFilePath = 'form.ui'
    
    def __init__(self, parentWidget):
        super().__init__(parentWidget)
        # open form having ui file path
        # bind events to this Form manipulator
        # can raise Exception - top prevent loading - аналог СтатусВозврата (1) в 1С
        
        moduleName = self.__class__.__module__
        module = sys.modules[moduleName]
        moduleDir = os.path.dirname(os.path.abspath(module.__file__)) 
        uiFilePath = os.path.join(moduleDir, self.uiFilePath)
            
        uic.loadUi(uiFilePath, self)
        #self.widgets = WFormWidgetHooker(self.form) # helper for the form
        #self.bindSignals()
        self.onOpen() # предопределенная процедура

    def closeEvent(self, event):
        if self.aboutToClose() == False: # вызов предопределенной процедуры
            event.ignore()
            return
        #self.reject()

    def bindSignals(self):
        '''Связать стандартные сигналы стандартных виджетов формы к предопределенным процедурам модуля.'''
        for child in self.dialog.children():
            childName = child.objectName()

            def bind(signalName):
                try:
                    getattr(child, signalName).connect(getattr(self, childName + '_' + signalName))
                except Exception as err:
                    err #print('Binding signals notice: %s\n' % str(err))

            if isinstance(child, QtGui.QTextEdit): 
                bind('textChanged')
            elif isinstance(child, QtGui.QCheckBox): 
                bind('stateChanged')
            elif isinstance(child, (WDateEdit, WDecimalEdit)):
                bind('edited') # check this classes before QLineEdit, because they are its descendants
            elif isinstance(child, QtGui.QLineEdit): 
                bind('textEdited')
            elif isinstance(child, QtGui.QPushButton): 
                bind('clicked')
            elif isinstance(child, QtGui.QSpinBox): 
                bind('valueChanged')
    
    def aboutToClose(self):
        return

    def onOpen(self):
        pass
    
    def widgetValidate(self):
        pass
