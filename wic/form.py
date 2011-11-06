import os, sys, importlib
from PyQt4 import QtGui, QtCore, uic
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit
from wic import orm
import wic


class WForm(QtGui.QDialog):
    '''QObject allows having signals - f.e. about some value selected.'''
    uiFilePath = 'form.ui' # absolute or relative path to the ui file
    iconPath = ':/icons/fugue/application-form.png'
    formTitle = 'Form'
    
    closed = QtCore.pyqtSignal()
    
    def __init__(self, parentWidget):
        super().__init__(parentWidget)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        if os.path.isabs(self.uiFilePath):
            uiFilePath = self.uiFilePath
        else: # ui file path is relative. extract module path
            moduleName = self.__class__.__module__
            module = sys.modules[moduleName] # module in which the Form class was defined
            moduleDir = os.path.dirname(os.path.abspath(module.__file__)) 
            uiFilePath = os.path.join(moduleDir, self.uiFilePath)
            
        uic.loadUi(uiFilePath, self)
        self.setupUi()
        self.setWindowTitle(self.formTitle)
        self.setWindowIcon(QtGui.QIcon(self.iconPath))
        self.on_open()
        
    def closeEvent(self, event):
        if self.on_close() == False: # вызов предопределенной процедуры
            event.ignore()
            return
        self.closed.emit()
        #self.reject()

    def on_close(self):
        pass

    def on_open(self):
        pass
    
    def setupUi(self):
        '''Initial setting up of the form. 
        Catalog item forms fill form fields with data from DB.'''
    


def setValue(widget, value):
    '''.'''
        
    if isinstance(widget, QtGui.QTextEdit): 
        widget.setPlainText(value)
    elif isinstance(widget, QtGui.QCheckBox): 
        #widget.blockSignals(True) # http://stackoverflow.com/questions/1856544/qcheckbox-is-it-really-not-possible-to-differentiate-between-user-induced-change
        widget.setChecked(value)
        #widget.blockSignals(False) 
    elif isinstance(widget, (WDateEdit, WDecimalEdit, QtGui.QSpinBox)):
        widget.setValue(value)
    elif isinstance(widget, (QtGui.QLineEdit, QtGui.QPushButton)): 
        widget.setText(value)

def getValue(widget):
    if isinstance(widget, QtGui.QTextEdit): 
        return widget.plainText()
    elif isinstance(widget, QtGui.QCheckBox): 
        return widget.isChecked()
    elif isinstance(widget, (WDateEdit, WDecimalEdit)): 
        return widget.value
    elif isinstance(widget, QtGui.QSpinBox): 
        return widget.value()
    elif isinstance(widget, (QtGui.QLineEdit, QtGui.QPushButton)): 
        return widget.text()



def openForm(formModulePath, formClassName= 'Form'):
    formModule = importlib.import_module(formModulePath)
    FormClass = getattr(formModule, formClassName)
    assert issubclass(FormClass, wic.form.WForm), 'This is not a WForm.'
    form = FormClass(None) # no parent widget for now
    window = wic.mainWindow.mdiArea.addSubWindow(form) # create subwindow with the form
    window.setWindowIcon(form.windowIcon())
    window.show()
    form.closed.connect(window.close) # when form closes - close subwindow too            


def openCatalogItemForm(catalogItem, formClassName= 'Form'):
    assert isinstance(catalogItem, orm.Model), 'Pass an item (model instance).'
    formModulePath = catalogItem.__class__.__module__
    
    formModule = importlib.import_module(formModulePath)
    FormClass = getattr(formModule, formClassName)
    assert issubclass(FormClass, wic.form.CatalogForm), 'This is not a CatalogForm: %s - %s' % (formModulePath, formClassName)
    form = FormClass(None, catalogItem) # no parent widget for now
    window = wic.mainWindow.mdiArea.addSubWindow(form) # create subwindow with the form
    window.setWindowIcon(form.windowIcon())
    window.show()
    form.closed.connect(window.close) # when form closes - close subwindow too            



class CatalogForm(WForm):
    '''Form of a catalog item.'''
    formTitle = 'Catalog item'
    iconPath = ':/icons/fugue/card-address.png'
    catalogItem = None
    
    def __init__(self, parentWidget, catalogItem):
        self.catalogItem = catalogItem
        super().__init__(parentWidget)

        
        
def putToForm(data, uiFilePath, dialog):
    'Загрузить форму с диска, заполнить поля данными data и вернуть форму'
    dialog = uic.loadUi(uiFilePath, QtGui.QDialog(dialog))
    for name, value in data.items():
        try: widget = getattr(dialog, name) # ищем нужный атрибут на форме
        except AttributeError: continue # такого нет
        if isinstance(widget, QtGui.QLineEdit):
            widget.setText(value)
            widget.home(False)
        elif isinstance(widget, QtGui.QPlainTextEdit):
            widget.setPlainText(value)
        elif isinstance(widget, QtGui.QLabel):
            widget.setText(value)
        elif isinstance(widget, QtGui.QComboBox):
            lineEdit = widget.lineEdit()
            if lineEdit: #Only editable combo boxes have a line edit
                lineEdit.setText(value)
        elif isinstance(widget, QtGui.QSpinBox):
            widget.setValue(int(value))
        elif isinstance(widget, QtGui.QCheckBox):
            widget.setChecked(value)
    return dialog


def getFromForm(dialog):
    data = {}
    for widget in dialog.children():
        value = None
        if isinstance(widget, QtGui.QLineEdit):
            value = widget.text()
        elif isinstance(widget, QtGui.QPlainTextEdit):
            value = widget.toPlainText()
        elif isinstance(widget, QtGui.QComboBox):
            lineEdit = widget.lineEdit()
            if lineEdit: #Only editable combo boxes have a line edit
                value = lineEdit.text()
        elif isinstance(widget, QtGui.QSpinBox):
            value = widget.value()
        elif isinstance(widget, QtGui.QCheckBox):
            value = bool(widget.isChecked())
        if value is not None:
            data[widget.objectName()] = value
    return data

