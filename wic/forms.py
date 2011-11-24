import os, sys, traceback
from PyQt4 import QtGui, QtCore, uic
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit
import orm
import wic



def setValue(widget, value):
    '''Automatically set a widget's value depending on its type.'''        
    if isinstance(widget, QtGui.QPlainTextEdit): 
        widget.setPlainText('' if value is None else str(value))
    elif isinstance(widget, QtGui.QTextEdit): 
        widget.setHtml('' if value is None else str(value))
    elif isinstance(widget, QtGui.QCheckBox): 
        widget.blockSignals(True) # http://stackoverflow.com/questions/1856544/qcheckbox-is-it-really-not-possible-to-differentiate-between-user-induced-change
        widget.setChecked(bool(value))
        widget.blockSignals(False) 
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
    if isinstance(widget, QtGui.QPlainTextEdit): 
        return widget.toPlainText()
    elif isinstance(widget, QtGui.QTextEdit): 
        return widget.toHtml()
    elif isinstance(widget, QtGui.QCheckBox): 
        return widget.isChecked()
    elif isinstance(widget, WDecimalEdit): 
        return widget.getValue()
    elif isinstance(widget, WDateEdit): 
        return widget.getDate()
    elif isinstance(widget, QtGui.QSpinBox): 
        return widget.value()
    elif isinstance(widget, (QtGui.QLineEdit, QtGui.QPushButton)): 
        return widget.text()
    elif isinstance(widget, QtGui.QComboBox):
        lineEdit = widget.lineEdit()
        if lineEdit: #Only editable combo boxes have a line edit
            return lineEdit.text()
    elif isinstance(widget, QtGui.QSpinBox):
        return widget.value()
    elif isinstance(widget, QtGui.QCheckBox):
        return bool(widget.isChecked())


class WFormWidgetHooker():
    '''Перехватчик виджетов формы. 
    Т.е. вместо form.checkBox.setChecked(True), можно писать form._.checkBox = True или form._['checkBox'] = True.'''
    def __init__(self, form):
        assert isinstance(form, QtGui.QWidget)
        super().__setattr__('_form', form) # to bypass overriden __setattr__
        
    def __setattr__(self, name, value):
        widget = getattr(self._form, name)
        setValue(widget, value)

    def __getattr__(self, name):
        widget = getattr(self._form, name)
        return getValue(widget)

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)



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
        
        self._ = WFormWidgetHooker(self)
        
        try:
            self.onOpen()
        except Exception:
            wic.mainWindow.messagesWindow.printMessage(''.join(traceback.format_exc()))
        
    def setupUi(self):
        '''Initial setting up of the form. 
        Catalog item forms fill form fields with data from DB.'''
        self.setWindowTitle(self.formTitle)
        self.setWindowIcon(QtGui.QIcon(self.iconPath))
        if self.uiFilePath: # not autogenerated
            uic.loadUi(self.uiFilePath, self)
            
        buttonBox = getattr(self, 'buttonBox', None)
        if buttonBox: # if button box is present - listen to its signals
            saveButton = buttonBox.button(buttonBox.Save)
            if saveButton: # change Save button's role
                buttonBox.addButton(saveButton, buttonBox.ApplyRole)
                saveButton.clicked.connect(self.onSave)
                saveShortCut = QtGui.QShortcut(QtGui.QKeySequence('F2'), self)
                saveShortCut.activated.connect(saveButton.animateClick)
            resetButton = buttonBox.button(buttonBox.Reset)
            if resetButton:
                resetButton.clicked.connect(self.fillFormFromItem)
            buttonBox.rejected.connect(self.reject)
        

    def done(self, resultCode): # accept/reject by default bypasses closeEvent
        super().done(resultCode)
        self.close()

    def closeEvent(self, event):
        if self.onClose() == False: # вызов предопределенной процедуры
            event.ignore()
            return
        self.closed.emit()

    def onClose(self):
        return

    def onOpen(self):
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
        self.formTitle = '%s item' % self.catalogItem.__class__ 
        super().setupUi()
        if not self.uiFilePath: # automatically generated form
            self.autoCreateWidgets()
        self.setupWidgets()            
        self.fillFormFromItem(self.catalogItem)

    def autoCreateWidgets(self):
        '''Automatically carete on the form widgets and labels for each catalog model field.'''
        self.formLayout = QtGui.QFormLayout(self)
        formLayout = self.formLayout
        formLayout.setMargin(2)
        formLayout.setObjectName('formLayout')
        for field in self.catalogItem.__class__:
            fieldName = field.name
            assert not hasattr(self, fieldName), 'Form already has attribute with name ""%s' % fieldName
            labelName = 'label_' + fieldName
            label = QtGui.QLabel(fieldName)
            label.setObjectName(labelName)
            widget = self.createWidgetForField(field)
            #widget.setObjectName(fieldName)
            setattr(self, fieldName, widget)
            label.setBuddy(widget)
            formLayout.addRow(label, widget)
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset 
                        | QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
        formLayout.addRow(self.buttonBox)
    
    def setupWidgets(self):
        '''Set up widgets which are mapped to catalog model fields. 
        Connect button box signals to the corresponding handlers.'''
        for field in self.catalogItem.__class__:
            widget = getattr(self, field.name, None)
            if widget:
                self.setupWidgetForField(widget, field)

    def fillFormFromItem(self, catalogItem):
        'Automatically fill the form fields using values from the catalog item fields.'
        for field in catalogItem.__class__:
            fieldName = field.name
            fieldValue = catalogItem[field]
            widget = getattr(self, fieldName, None)
            if widget:
                setValue(widget, fieldValue)
        
    def fillItemFromForm(self, catalogItem):
        'Automatically fill the item field values from the corresponding form widgets.'
        for field in catalogItem.__class__:
            fieldName = field.name
            widget = getattr(self, fieldName, None)
            if widget:
                fieldValue = getValue(widget)
                if isinstance(field, (orm.IdField, orm.RecordIdField)) and not fieldValue:
                    fieldValue = None
                setattr(catalogItem, fieldName, fieldValue)
            
    def onSave(self):
        ''
        wic.w.printMessage('save!')
        catalogItem = self.catalogItem
        self.fillItemFromForm(catalogItem)
        catalogItem.save()
        
        # update item id and timestamp on the form
        idWidget = getattr(self, '_id', None)
        if idWidget:
            setValue(idWidget, catalogItem._id)
        timestampWidget = getattr(self, '_timestamp', None)
        if timestampWidget:
            setValue(timestampWidget, catalogItem._timestamp)


    @staticmethod    
    def createWidgetForField(field):
        assert isinstance(field, orm.Field)
        if isinstance(field, (orm.CharField, orm.IntegerField, orm.IdField, orm.RecordIdField, orm.DateTimeField)):
            return QtGui.QLineEdit()
        elif isinstance(field, orm.DecimalField):
            return WDecimalEdit()
        elif isinstance(field, orm.DateField):
            return WDateEdit()
        elif isinstance(field, orm.BooleanField):
            return QtGui.QCheckBox(field.name)
        elif isinstance(field, orm.TextField):
            return QtGui.QPlainTextEdit()
        raise Exception('Could not create a widget for field %s' % field)

    @staticmethod
    def setupWidgetForField(widget, field):
        '''Set up a widget which corresponds to an model field - only the details related to data entering to appearance.
        The widget might be autocreated or one from a *.ui file.'''
        assert isinstance(field, orm.Field) and isinstance(widget, QtGui.QWidget)
        if isinstance(field, orm.CharField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setMaxLength(field.maxLength)
        elif isinstance(field, (orm.IdField, orm.RecordIdField)):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setValidator(QtGui.QIntValidator())
        elif isinstance(field, orm.DateTimeField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setInputMask('9999-99-99 99:99:99.999999;0')
        elif isinstance(field, orm.DecimalField):
            if isinstance(widget, WDecimalEdit):
                widget.setMaxDigits(field.maxDigits)
                widget.setFractionDigits(field.fractionDigits)

