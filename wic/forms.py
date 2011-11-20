import os, sys, traceback
from PyQt4 import QtGui, QtCore, uic
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit
import orm
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
        
        if self.uiFilePath: # not autogenerated
            if not os.path.isabs(self.uiFilePath): # ui file path is relative. extract module path
                module = sys.modules[self.__class__.__module__] # module in which the Form class was defined
                moduleDir = os.path.dirname(os.path.abspath(module.__file__)) 
                self.uiFilePath = os.path.join(moduleDir, self.uiFilePath)
        
        self.setupUi()
        
        try:
            self.on_open()
        except Exception:
            wic.mainWindow.messagesWindow.printMessage(''.join(traceback.format_exc()))
        
    def setupUi(self):
        '''Initial setting up of the form. 
        Catalog item forms fill form fields with data from DB.'''
        self.setWindowTitle(self.formTitle)
        self.setWindowIcon(QtGui.QIcon(self.iconPath))
        if self.uiFilePath: # not autogenerated
            uic.loadUi(self.uiFilePath, self)

    def done(self, resultCode): # accept/reject by default bypasses closeEvent
        super().done(resultCode)
        self.close()

    def closeEvent(self, event):
        if self.on_close() == False: # вызов предопределенной процедуры
            event.ignore()
            return
        self.closed.emit()

    def on_close(self):
        return

    def on_open(self):
        return
    


def openForm(FormClass):
    assert issubclass(FormClass, WForm), 'This is not a WForm.'
    form = FormClass(None) # no parent widget for now
    window = wic.mainWindow.mdiArea.addSubWindow(form) # create subwindow with the form
    window.setWindowIcon(form.windowIcon())
    window.show()
    form.closed.connect(window.close) # when form closes - close subwindow too            


def openCatalogItemForm(catalogItem, FormClass= None):
    assert isinstance(catalogItem, orm.Model), 'Pass an item (model instance).'
    if FormClass is None:
        formModulePath = catalogItem.__class__.__module__
        FormClass = getattr(sys.modules[formModulePath], 'Form')
    assert issubclass(FormClass, CatalogForm), 'This is not a CatalogForm'
    
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
        self.formTitle = '%s item' % catalogItem.__class__ 
        super().setupUi()
        if not self.uiFilePath: # automatically generated form
            self.formLayout = QtGui.QFormLayout(self)
            formLayout = self.formLayout
            formLayout.setMargin(2)
            formLayout.setObjectName('formLayout')
            for field in catalogItem.__class__:
                fieldName = field.name
                assert not hasattr(self, fieldName), 'Form already has attribute with name ""%s' % fieldName
                labelName = 'label_' + fieldName
                label = QtGui.QLabel(fieldName)
                label.setObjectName(labelName)
                widget = createWidgetFromField(field)
                #widget.setObjectName(fieldName)
                setattr(self, fieldName, widget)
                label.setBuddy(widget)
                formLayout.addRow(label, widget)
            
            self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset 
                            | QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
            formLayout.addRow(self.buttonBox)
            
        buttonBox = getattr(self, 'buttonBox', None)
        if buttonBox: # if button box is present - listen to its signals
            saveButton = buttonBox.button(buttonBox.Save)
            if saveButton: # change Save button's role
                buttonBox.addButton(saveButton, buttonBox.ApplyRole)
                saveButton.clicked.connect(self.save)
                saveShortCut = QtGui.QShortcut(QtGui.QKeySequence('F2'), self)
                saveShortCut.activated.connect(saveButton.animateClick)
            resetButton = buttonBox.button(buttonBox.Reset)
            if resetButton:
                resetButton.clicked.connect(self.fillFormFromItem)
            buttonBox.rejected.connect(self.reject)
            
        self.fillFormFromItem()

    def fillFormFromItem(self):
        'Automatically fill the form fields using values from the catalog item fields.'
        catalogItem = self.catalogItem
        for field in catalogItem.__class__:
            fieldName = field.name
            fieldValue = catalogItem[field]
            widget = getattr(self, fieldName, None)
            if widget:
                setValue(widget, fieldValue)
        
#    def fillItemFromForm(self):
#        'Automatically fill the form fields using values from the catalog item fields.'
#        catalogItem = self.catalogItem
#        for field in catalogItem.__class__:
#            fieldName = field.name
#            fieldValue = catalogItem[field]
#            widget = getattr(self, fieldName, None)
#            if widget:
#                setValue(widget, fieldValue)
        
            
    def save(self):
        ''
        wic.w.printMessage('save!')
        catalogItem = self.catalogItem
        for field in catalogItem.__class__:
            fieldName = field.name
            widget = getattr(self, fieldName, None)
            if widget:
                fieldValue = getValue(widget)
                if isinstance(field, (orm.IdField, orm.RecordIdField)) and not fieldValue:
                    fieldValue = None
                setattr(catalogItem, fieldName, fieldValue)
        catalogItem.save()
        idWidget = getattr(self, '_id', None)
        if idWidget:
            setValue(idWidget, catalogItem._id)


        
def createWidgetFromField(field):
    assert isinstance(field, orm.Field), 'Pass a Field instance.'
    if isinstance(field, orm.StringField):
        widget = QtGui.QLineEdit()
        widget.setMaxLength(field.maxLength)
    elif isinstance(field, (orm.IntegerField, orm.IdField, orm.RecordIdField)):
        widget = QtGui.QLineEdit()
        widget.setValidator(QtGui.QIntValidator())
    elif isinstance(field, orm.DateTimeField):
        widget = QtGui.QLineEdit()
        widget.setInputMask('9999-99-99 99:99:99.999999;0')
    elif isinstance(field, orm.DecimalField):
        widget = WDecimalEdit()
        widget.setMaxDigits(field.column.props['maxDigits'])
        widget.setFractionDigits(field.column.props['fractionDigits'])
    elif isinstance(field, orm.DateField):
        widget = WDateEdit()
    elif isinstance(field, orm.BooleanField):
        widget = QtGui.QCheckBox(field.name)
    else: # any other - treat as text
#        widget = QtGui.QLineEdit()
        raise Exception('Could not find a widget for field %s' % field)
    return widget


def setValue(widget, value):
    '''Automatically set a widget's value depending on its type.'''        
    if isinstance(widget, (QtGui.QTextEdit, QtGui.QPlainTextEdit)): 
        widget.setPlainText(str(value))
    elif isinstance(widget, QtGui.QCheckBox): 
        #widget.blockSignals(True) # http://stackoverflow.com/questions/1856544/qcheckbox-is-it-really-not-possible-to-differentiate-between-user-induced-change
        widget.setChecked(bool(value))
        #widget.blockSignals(False) 
    elif isinstance(widget, WDateEdit):
        widget.setDate(value)
    elif isinstance(widget, (WDecimalEdit, QtGui.QSpinBox)):
        widget.setValue(value)
    elif isinstance(widget, QtGui.QLineEdit):
        widget.setText('' if value is None else str(value))
        widget.home(False)
    elif isinstance(widget, QtGui.QPushButton): 
        widget.setText(str(value))
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

def getValue(widget):
    '''Automatically extract a widget's value depending on its type.'''
    if isinstance(widget, QtGui.QTextEdit): 
        return widget.plainText()
    elif isinstance(widget, QtGui.QCheckBox): 
        return widget.isChecked()
    elif isinstance(widget, WDecimalEdit): 
        return widget.value
    elif isinstance(widget, WDateEdit): 
        return widget.date
    elif isinstance(widget, QtGui.QSpinBox): 
        return widget.value()
    elif isinstance(widget, (QtGui.QLineEdit, QtGui.QPushButton)): 
        return widget.text()
    elif isinstance(widget, QtGui.QPlainTextEdit):
        return widget.toPlainText()
    elif isinstance(widget, QtGui.QComboBox):
        lineEdit = widget.lineEdit()
        if lineEdit: #Only editable combo boxes have a line edit
            return lineEdit.text()
    elif isinstance(widget, QtGui.QSpinBox):
        return widget.value()
    elif isinstance(widget, QtGui.QCheckBox):
        return bool(widget.isChecked())
