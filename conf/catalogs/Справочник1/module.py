import os, sys
from PyQt4 import QtCore, QtGui, uic
from wic.w import printMessage
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit


class Controller(): # Form manipulator
    '''Controller which responds to user actions on the form.
    It is created by the engine passing context info needed for initialization.'''
    
    def __init__(self, uiFilePath= None):
        # open form having ui file path
        # bind events to this Form manipulator
        # can raise Exception - top prevent loading - аналог СтатусВозврата (1) в 1С
        if not uiFilePath:
            curDir = os.path.dirname(os.path.abspath(__file__))
            uiFilePath = os.path.join(curDir, 'form.ui')
            
        formClass, formBaseClass = uic.loadUiType(uiFilePath)
        if not issubclass(formBaseClass, QtGui.QDialog):
            printMessage('<b>Форма не загружена - ожидается QDialog: </b>' + uiFilePath)
            return

        class WFormClass(formClass, QtGui.QDialog):
            def __init__(self, parent, module):
                super().__init__(parent)
                self.setupUi(self)
                self.finished.connect(self.close)
                self.module = module
                module.form = self # set reference to the form
                self.bindSignals()
            
            def closeEvent(self, event):
                if self.aboutToClose() == False: # вызов предопределенной процедуры
                    event.ignore()
                    self.show()
                    return
                self.parentWidget().close() # close sub window

            def bindSignals(self):
                'Связать стандартные сигналы стандартных виджетов формы к предопределенным процедурам модуля.'
                for child in self.children():
                    childName = child.objectName()

                    def bind(signalName):
                        try:
                            getattr(child, signalName).connect(getattr(self.module, childName + '_' + signalName))
                        except Exception as err:
                            err #print('Binding signals notice: %s\n' % str(err))

                    if isinstance(child, QtGui.QTextEdit): bind('textChanged')
                    elif isinstance(child, QtGui.QCheckBox): bind('stateChanged')
                    elif isinstance(child, (WDateEdit, WDecimalEdit)): bind('edited') # check this classes before QLineEdit, because they are its descendants
                    elif isinstance(child, QtGui.QLineEdit): bind('textEdited')
                    elif isinstance(child, QtGui.QPushButton): bind('clicked')
                    elif isinstance(child, QtGui.QSpinBox): bind('valueChanged')



        #uiFilename = os.path.join(os.path.dirname(filePath), 'form.ui')
        #form = uic.loadUi(uiFilename, WFormClass(None)) # create form
        self.form = WFormClass(None, module) # create form
        window = mainWindow.mdiArea.addSubWindow(self.form) # create subwindow with the form
        window.show()
        self.widgets = WFormWidgetHooker(self.form) # helper for the form
        self.onOpen() # предопределенная процедура

    
    def onClose(self):
        pass
    
    def onOpen(self):
        pass
    
    def widgetValidate(self):
        pass
    
    def __call__(self):
        '''return some values from the called form?'''