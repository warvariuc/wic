import os, sys, traceback

from PyQt5 import QtGui, QtCore, uic, QtWidgets

import wic
import wic.widgets


class FormNotFoundError(Exception):
    """Raised when a form is not found
    """


def value(widget, value=wic.MISSING):
    """Get/set widget value depending on its type.

    Args:
        widget(QWidget): widget from/which to get/set a value
        value: if specified - set that value, otherwise get widget's value
    """
    if value is wic.MISSING:
        return get_value(widget)
    return set_value(widget, value)


def set_value(widget, value):
    """Automatically set a widget's value depending on its type.
    """
    if isinstance(widget, QtWidgets.QPlainTextEdit):
        widget.setPlainText('' if value is None else str(value))
    elif isinstance(widget, QtWidgets.QTextEdit):
        widget.setHtml('' if value is None else str(value))
    elif isinstance(widget, QtWidgets.QCheckBox):
        # http://stackoverflow.com/questions/1856544/qcheckbox-is-it-really-not-possible-to-differentiate-between-user-induced-change
        widget.blockSignals(True)
        widget.setChecked(bool(value))
        widget.blockSignals(False)
    # this goes before checking QLineEdit, because WDateEdit is subclass of QLineEdit
    elif isinstance(widget, wic.widgets.DateEdit):
        widget.setDate(value)
    elif isinstance(widget, (wic.widgets.DecimalEdit, QtWidgets.QSpinBox)):
        widget.setValue(value)
    elif isinstance(widget, wic.widgets.CatalogItemWidget):
        widget.setItem(value)
    elif isinstance(widget, QtWidgets.QLineEdit):
        widget.setText('' if value is None else str(value))
        widget.home(False)
    elif isinstance(widget, QtWidgets.QPushButton):
        widget.setText(str(value))
    elif isinstance(widget, QtWidgets.QLabel):
        widget.setText(value)
    elif isinstance(widget, QtWidgets.QComboBox):
        lineEdit = widget.lineEdit()
        if lineEdit:
            # Only editable combo boxes have a line edit
            lineEdit.setText(value)
        if widget.isEditable():
            # if the combo box is editable - set the text
            return widget.lineEdit.setText(value)
        else:
            # find item with the given value and set it as current
            widget.setCurrentIndex(widget.findData(value))
    elif isinstance(widget, QtWidgets.QSpinBox):
        widget.setValue(int(value))
    elif isinstance(widget, QtWidgets.QCheckBox):
        widget.setChecked(value)


def get_value(widget):
    """Automatically extract a widget's value depending on its type.
    """
    if isinstance(widget, QtWidgets.QPlainTextEdit):
        return widget.toPlainText()
    elif isinstance(widget, QtWidgets.QTextEdit):
        return widget.toHtml()
    elif isinstance(widget, QtWidgets.QCheckBox):
        return widget.isChecked()
    elif isinstance(widget, wic.widgets.DecimalEdit):
        return widget.value()
    elif isinstance(widget, wic.widgets.DateEdit):
        return widget.date()
    elif isinstance(widget, wic.widgets.CatalogItemWidget):
        return widget.item()
    elif isinstance(widget, QtWidgets.QSpinBox):
        return widget.value()
    elif isinstance(widget, (QtWidgets.QLineEdit, QtWidgets.QPushButton)):
        return widget.text()
    elif isinstance(widget, QtWidgets.QComboBox):
        if widget.isEditable():
            # if the combo box is editable - return the text
            return widget.currentText()
        else:
            # otherwise return the value of the selectem item
            return widget.itemData(widget.currentIndex())
    elif isinstance(widget, QtWidgets.QSpinBox):
        return widget.value()
    elif isinstance(widget, QtWidgets.QCheckBox):
        return widget.isChecked()


class FormWidgetsProxy():
    """Proxy for form widgets. 
    I.e. instead of `form.checkBox.setChecked(True)`, you can write `form._.checkBox = True` or `form._['checkBox'] = True`.
    """
    def __init__(self, form):
        assert isinstance(form, QtWidgets.QWidget)
        super().__setattr__('_form', form) # to bypass overriden __setattr__

    def __setattr__(self, name, value):
        widget = getattr(self._form, name)
        set_value(widget, value)

    def __getattr__(self, name):
        widget = getattr(self._form, name)
        return get_value(widget)

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)


class Form(QtWidgets.QDialog):
    """Base class for user forms.
    """
    _ui_file_path = 'form.ui' # absolute or relative path to the ui file
    _iconPath = ':/icons/fugue/application-form.png'
    _form_title = 'Form'
    # Name of the form's default button box widget which usually has button "Reset", "
    _button_box_name = 'button_box'

    # emitted when the form is closing
    closed = QtCore.pyqtSignal()

    def __init__(self, **kwargs):
        super().__init__(None)  # no parent upon creation
        self.__dict__.update(kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.button_box = None

        if self._ui_file_path:
            # not autogenerated
            if not os.path.isabs(self._ui_file_path):
                # ui file path is relative. extract module path
                # module in which the Form class was defined
                module = sys.modules[self.__class__.__module__]
                module_dir = os.path.dirname(os.path.abspath(module.__file__))
                self._ui_file_path = os.path.join(module_dir, self._ui_file_path)

        self.setupUi()

        self._ = FormWidgetsProxy(self)

        try:
            self.on_open()
        except Exception:
            traceback.print_exc()

    def setupUi(self):
        """Initial setting up of the form. 
        Catalog item forms fill form fields with data from DB.
        """
        if not self.windowTitle():
            # the title was not set yet
            self.setWindowTitle(self._form_title)
        self.setWindowIcon(QtGui.QIcon(self._iconPath))
        if self._ui_file_path:
            # not autogenerated
            uic.loadUi(self._ui_file_path, self)
        self._setup_button_box()
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu_requested)

    def _setup_button_box(self):
        # if button box is present - listen to its signals
        button_box = getattr(self, self._button_box_name, None)
        if not button_box:
            return
        save_button = button_box.button(button_box.Save)
        if save_button:
            # change Save button's role
            button_box.addButton(save_button, button_box.ApplyRole)
            save_button.clicked.connect(self.onSave)
            save_shortCut = QtWidgets.QShortcut(QtGui.QKeySequence('F2'), self)
            save_shortCut.activated.connect(save_button.animateClick)
        reset_button = button_box.button(button_box.Reset)
        if reset_button:
            reset_button.clicked.connect(self.on_reset)
        button_box.rejected.connect(self.reject)

    def on_context_menu_requested(self, coord):
        from wic import menus

        menu = QtWidgets.QMenu(self)
        menus.add_actions_to_menu(menu, menus.create_action(
            menu, 'Save this form into a *.ui file.', self.save_form_to_ui_file))
        menu.popup(self.mapToGlobal(coord))

    def save_form_to_ui_file(self):
        from PyQt5.QtDesigner import QFormBuilder
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            parent=self, caption='Save file', directory='', filter='Forms (*.ui)')
        if not file_path:
            return
        file = QtCore.QFile(file_path)
        file.open(file.WriteOnly)
        form_builder = QFormBuilder()
        form_builder.save(file, self)

    def done(self, resultCode):
        # accept/reject by default bypasses closeEvent
        super().done(resultCode)
        self.close()

    def closeEvent(self, event):
        # check the callback
        if self.on_close() is False:
            event.ignore()
            return
        self.closed.emit()

    def on_close(self):
        """Callback called when the form is about to close. If it returns False, the app
        prevents the closing.
        """

    def on_open(self):
        """Callback called when the form is about to open.
        """

    def on_reset(self):
        """Callback called when the form's "Reset" button is clicked.
        """

    def show_warning(self, title, text):
        """Convenience function to show a warning message box.
        """
        QtWidgets.QMessageBox.warning(self, title, text)

    def show_information(self, title, text):
        """Convenience function to show an information message box.
        """
        QtWidgets.QMessageBox.information(self, title, text)


def open_form(FormClass, modal=False, **kwargs):
    if isinstance(FormClass, str):
        FormClass = wic.get_object_by_path(FormClass)
    assert issubclass(FormClass, Form), 'This is not a WForm.'
    form = FormClass(**kwargs)  # no parent widget for now
    if modal:
        return form.exec()
    wic._app.addSubWindow(form)
    return form


from . import catalog
