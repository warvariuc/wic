import os, sys, importlib
from PyQt4 import QtGui, QtCore, uic
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit
from wic import orm
import wic


class WForm(QtGui.QDialog):
    '''Base for user forms.'''
    
    uiFilePath = 'form.ui' # absolute or relative path to the ui file
    iconPath = ':/icons/fugue/application-form.png'
    formTitle = 'Form'
    
    closed = QtCore.pyqtSignal() # emitted when the form is closing
    
    def __init__(self, parentWidget):
        super().__init__(parentWidget)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        if not self.uiFilePath == '<auto>':
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

    def setupUi(self):
        '''Initial setting up of the form.
        Dynamically create form fields, if no ui file is supplied. 
        Fill form fields with data from DB.'''
        catalogItem = self.catalogItem
        if self.uiFilePath == '<auto>':
            self.formLayout = QtGui.QFormLayout(self)
            formLayout = self.formLayout
            formLayout.setMargin(2)
            #self.gridLayout.setObjectName('gridLayout')
            for field in catalogItem.__class__:
                fieldName = field.name
                assert not hasattr(self, fieldName), 'Form already has attribute with name ""%s' % fieldName
                labelName = 'label_' + fieldName
                label = QtGui.QLabel(labelName, self)
                fieldValue = catalogItem[field]
                #formLayout.addRow( QWidget * label, QWidget * field)
                formLayout.addRow(label)
                print(fieldValue)
            pass
#        self.label = QtGui.QLabel(Dialog)
#        self.label.setText(QtGui.QApplication.translate("Dialog", "Идентификатор", None, QtGui.QApplication.UnicodeUTF8))
#        self.label.setObjectName(_fromUtf8("label"))
#        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
#        self.identifier = QtGui.QLineEdit(Dialog)
#        self.identifier.setObjectName(_fromUtf8("identifier"))
#        self.gridLayout.addWidget(self.identifier, 1, 0, 1, 2)
#        self.label_2 = QtGui.QLabel(Dialog)
#        self.label_2.setText(QtGui.QApplication.translate("Dialog", "Название", None, QtGui.QApplication.UnicodeUTF8))
#        self.label_2.setObjectName(_fromUtf8("label_2"))
#        self.gridLayout.addWidget(self.label_2, 2, 0, 1, 1)
#        self.name = QtGui.QLineEdit(Dialog)
#        self.name.setObjectName(_fromUtf8("name"))
#        self.gridLayout.addWidget(self.name, 3, 0, 1, 2)
#        self.label_3 = QtGui.QLabel(Dialog)
#        self.label_3.setText(QtGui.QApplication.translate("Dialog", "Комментарий", None, QtGui.QApplication.UnicodeUTF8))
#        self.label_3.setObjectName(_fromUtf8("label_3"))
#        self.gridLayout.addWidget(self.label_3, 4, 0, 1, 1)
#        self.description = QtGui.QPlainTextEdit(Dialog)
#        self.description.setObjectName(_fromUtf8("description"))
#        self.gridLayout.addWidget(self.description, 5, 0, 1, 2)
#        self.buttonBox = QtGui.QDialogButtonBox(Dialog)
#        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
#        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
#        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
#        self.gridLayout.addWidget(self.buttonBox, 6, 1, 1, 1)
#        self.label.setBuddy(self.identifier)
#        self.label_2.setBuddy(self.name)

        
        
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

