import os, sys
from PyQt4 import QtCore, QtGui, uic
from wic.w import printMessage
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit


class Form(QtGui.QWidget): # Form manipulator
    '''QObject allows having signals - f.e. about some value selected.'''
    
    def __init__(self, parentWidget):
        super().__init__(parentWidget)
        # open form having ui file path
        # bind events to this Form manipulator
        # can raise Exception - top prevent loading - аналог СтатусВозврата (1) в 1С
        
        curDir = os.path.dirname(os.path.abspath(__file__))
        uiFilePath = os.path.join(curDir, 'form.ui')
            
        dialogUi, uiQtClass = uic.loadUiType(uiFilePath)
        if not issubclass(uiQtClass, QtGui.QDialog):
            printMessage('<b>Форма не загружена - ожидается QDialog: </b>' + uiFilePath)
            return

        class Dialog(uiQtClass, dialogUi):
            def __init__(self, parent):
                super().__init__(parent)
                self.finished.connect(self.close)
                self.setupUi(parent)
            

        self.dialog = Dialog(self) # create form
        #self.widgets = WFormWidgetHooker(self.form) # helper for the form
        #self.bindSignals()
        self.onOpen() # предопределенная процедура

    def closeEvent(self, event):
        print('closeEvent2')
        if self.aboutToClose() == False: # вызов предопределенной процедуры
            event.ignore()
            #self.show()
            return
        self.parentWidget().close() # close sub window

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
    