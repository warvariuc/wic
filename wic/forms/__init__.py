__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import os, sys, traceback
from PyQt4 import QtGui, QtCore, uic
import orm
from orm import Nil
import wic
from wic.widgets import WDateEdit, WDecimalEdit, WCatalogItemWidget


class FormNotFoundError(Exception):
    """Raised when a form is not found
    """


def value(widget, value = Nil):
    """Get/set widget value depending on its type.
    @param widget: QWidget from/which to get/set a value
    @param value: if specified - set that value, otherwise get widget's value
    """
    if value is Nil:
        return getValue(widget)
    else:
        return setValue(widget, value)


def setValue(widget, value):
    """Automatically set a widget's value depending on its type.
    """
    if isinstance(widget, QtGui.QPlainTextEdit):
        widget.setPlainText('' if value is None else str(value))
    elif isinstance(widget, QtGui.QTextEdit):
        widget.setHtml('' if value is None else str(value))
    elif isinstance(widget, QtGui.QCheckBox):
        widget.blockSignals(True) # http://stackoverflow.com/questions/1856544/qcheckbox-is-it-really-not-possible-to-differentiate-between-user-induced-change
        widget.setChecked(bool(value))
        widget.blockSignals(False)
    elif isinstance(widget, WDateEdit): # this goes before checking QLineEdit, because WDateEdit is subclass of QLineEdit 
        widget.setDate(value)
    elif isinstance(widget, (WDecimalEdit, QtGui.QSpinBox)):
        widget.setValue(value)
    elif isinstance(widget, WCatalogItemWidget):
        widget.setItem(value)
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
        if widget.isEditable(): # if the combo box is editable - set the text 
            return widget.lineEdit.setText(value)
        else: # find item with the given value and set it as current
            widget.setCurrentIndex(widget.findData(value))
    elif isinstance(widget, QtGui.QSpinBox):
        widget.setValue(int(value))
    elif isinstance(widget, QtGui.QCheckBox):
        widget.setChecked(value)


def getValue(widget):
    """Automatically extract a widget's value depending on its type.
    """
    if isinstance(widget, QtGui.QPlainTextEdit):
        return widget.toPlainText()
    elif isinstance(widget, QtGui.QTextEdit):
        return widget.toHtml()
    elif isinstance(widget, QtGui.QCheckBox):
        return widget.isChecked()
    elif isinstance(widget, WDecimalEdit):
        return widget.value()
    elif isinstance(widget, WDateEdit):
        return widget.date()
    elif isinstance(widget, WCatalogItemWidget):
        return widget.item()
    elif isinstance(widget, QtGui.QSpinBox):
        return widget.value()
    elif isinstance(widget, (QtGui.QLineEdit, QtGui.QPushButton)):
        return widget.text()
    elif isinstance(widget, QtGui.QComboBox):
        if widget.isEditable(): # if the combo box is editable - return the text
            return widget.currentText()
        else: # otherwise return the value of the selectem item 
            return widget.itemData(widget.currentIndex())
    elif isinstance(widget, QtGui.QSpinBox):
        return widget.value()
    elif isinstance(widget, QtGui.QCheckBox):
        return widget.isChecked()


class WFormWidgetsProxy():
    """Proxy for form widgets. 
    I.e. instead of `form.checkBox.setChecked(True)`, you can write `form._.checkBox = True` or `form._['checkBox'] = True`.
    """
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
    """Base for user forms.
    """

    _uiFilePath = 'form.ui' # absolute or relative path to the ui file
    _iconPath = ':/icons/fugue/application-form.png'
    _formTitle = 'Form'

    closed = QtCore.pyqtSignal() # emitted when the form is closing

    def __init__(self, **kwargs):
        super().__init__(None) # no parent upon creation
        self.__dict__.update(kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        if self._uiFilePath: # not autogenerated
            if not os.path.isabs(self._uiFilePath): # ui file path is relative. extract module path
                module = sys.modules[self.__class__.__module__] # module in which the Form class was defined
                moduleDir = os.path.dirname(os.path.abspath(module.__file__))
                self._uiFilePath = os.path.join(moduleDir, self._uiFilePath)

        self.setupUi()

        self._ = WFormWidgetsProxy(self)

        try:
            self.onOpen()
        except Exception:
            traceback.print_exc()

    def setupUi(self):
        """Initial setting up of the form. 
        Catalog item forms fill form fields with data from DB.
        """
        if not self.windowTitle(): # if the title was not set yet
            self.setWindowTitle(self._formTitle)
        self.setWindowIcon(QtGui.QIcon(self._iconPath))
        if self._uiFilePath: # not autogenerated
            uic.loadUi(self._uiFilePath, self)

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
                resetButton.clicked.connect(self.onReset)
            buttonBox.rejected.connect(self.reject)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onContextMenuRequested)

    def onContextMenuRequested(self, coord):
        from wic import menus
        menu = QtGui.QMenu(self)
        menus.addActionsToMenu(menu, (menus.createAction(menu, 'Save this form into a *.ui file.', self.saveFormToUi),))
        menu.popup(self.mapToGlobal(coord))

    def saveFormToUi(self):
        from PyQt4.QtDesigner import QFormBuilder
        filePath = QtGui.QFileDialog.getSaveFileName(parent = self, caption = 'Save file', directory = '', filter = 'Forms (*.ui)')
        if filePath:
            file = QtCore.QFile(filePath)
            file.open(file.WriteOnly)
            formBuilder = QFormBuilder()
            formBuilder.save(file, self)

    def done(self, resultCode): # accept/reject by default bypasses closeEvent
        super().done(resultCode)
        self.close()

    def closeEvent(self, event):
        if self.onClose() == False: # вызов предопределенной процедуры
            event.ignore()
            return
        self.closed.emit()

    def onClose(self):
        ""

    def onOpen(self):
        ""

    def onReset(self):
        ""

    def showWarning(self, title, text):
        """Convenience function to show a warning message box."""
        QtGui.QMessageBox.warning(self, title, text)

    def showInformation(self, title, text):
        """Convenience function to show an information message box."""
        QtGui.QMessageBox.information(self, title, text)


def openForm(FormClass, *args, modal = False, **kwargs):
    if isinstance(FormClass, str):
        FormClass = wic.get_object_by_path(FormClass)
    assert issubclass(FormClass, WForm), 'This is not a WForm.'
    form = FormClass(*args, **kwargs) # no parent widget for now
    if modal:
        return form.exec()
    wic.app.addSubWindow(form)
    return form



from . import catalog
from .catalog import openCatalogForm, openCatalogItemForm, CatalogItemForm
