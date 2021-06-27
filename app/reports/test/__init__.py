from PyQt5 import QtCore, QtGui

from wic.forms import Form, set_value, get_value
from wic.datetime import Date, RelDelta
import app


class Form(Form):

    _iconPath = ':/icons/fugue/leaf-wormhole.png'
    _formTitle = 'Test module and form'

    def onOpen(self): # called by the system after it loads the Form
        print('The form has opened.')

        self._.dteShowSelector = self.dateEdit.selectorVisible
        self._.dateEdit = Date.today()
        self._.decimalEdit = '20000000.1251'
        self.updateInfoAboutDecimalEdit()

    def onClose(self): # Form is asked to be closed
#        if QtGui.QMessageBox.question(self, 'Подтверждение', 'Вы действительно хотите закрыть форму?',
#                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
#            return False
        print('The form is closing.')

    def on_dceShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.selectorVisible = state
        self.decimalEdit.setFocus()

    def on_dceNonNegative_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.nonNegative = state

    def on_dceSeparateThousands_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.thousandsSeparated = state

    def on_decimalEdit_edited(self):
        print('DecimalEdit edited. New value:', self._.decimalEdit)

    def on_dteShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.dateEdit.selectorVisible = state

    def on_dateEdit_edited(self):
        print('DateEdit edited. New value:', self._.dateEdit)

    @QtCore.pyqtSlot()
    def on_testGm_clicked(self):
        app.test()

    def on_dceTotalDigits_valueChanged(self, text):
        self.decimalEdit.maxDigits = int(text)
        self.updateInfoAboutDecimalEdit()

    def on_dceFractionDigits_valueChanged(self, text):
        self.decimalEdit.fractionDigits = int(text)
        self.updateInfoAboutDecimalEdit()

    def updateInfoAboutDecimalEdit(self):
        self._.dceShowSelector = self.decimalEdit.selectorVisible
        self._.dceTotalDigits = self.decimalEdit.maxDigits
        self._.dceFractionDigits = self.decimalEdit.fractionDigits
        self._.dceNonNegative = self.decimalEdit.nonNegative
        self._.dceSeparateThousands = self.decimalEdit.thousandsSeparated
