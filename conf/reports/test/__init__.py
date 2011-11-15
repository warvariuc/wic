import os, sys
from PyQt4 import QtCore, QtGui

from wic import w
from wic.forms import WForm, setValue, getValue
from datetime import date as Date
from dateutil.relativedelta import relativedelta as RelDelta
import conf as globalModule


class Form(WForm):

    iconPath = ':/icons/fugue/leaf-wormhole.png'
    formTitle = 'Тестовые модуль и форма'

    def on_open(self): # called by the system after it loads the Form
        w.printMessage('Форма загружена.')

        self.dteShowSelector.setChecked(self.dateEdit.getShowSelector())
        setValue(self.dateEdit, Date.today())
        setValue(self.decimalEdit, '20000000.1251')
        self.updateInfoAboutDecimalEdit()

    def on_close(self): # Form is asked to be closed
#        if QtGui.QMessageBox.question(self, 'Подтверждение', 'Вы действительно хотите закрыть форму?',
#                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
#            return False
        w.printMessage('Форма закрывается.')

    def on_dceShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.showSelector = state
        self.decimalEdit.setFocus()

    def on_dceNonNegative_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.nonNegative = state

    def on_dceSeparateThousands_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.separateThousands = state

    def on_decimalEdit_edited(self):
        w.printMessage('WDecimalEdit отредактирован. Новое значение: %s' % self.decimalEdit.value)

    def on_dteShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.dateEdit.showSelector = state

    def on_dateEdit_edited(self):
        w.printMessage('WDateEdit отредактирован. Новое значение: %s' % self.dateEdit.date)

    @QtCore.pyqtSlot()
    def on_testGm_clicked(self):
        globalModule.test()

    def on_dceTotalDigits_valueChanged(self, text):
        self.decimalEdit.setTotalDigits(int(text))
        self.updateInfoAboutDecimalEdit()

    def on_dceFractionDigits_valueChanged(self, text):
        self.decimalEdit.setFractionDigits(int(text))
        self.updateInfoAboutDecimalEdit()

    def updateInfoAboutDecimalEdit(self):
        setValue(self.dceShowSelector, self.decimalEdit.showSelector)
        setValue(self.dceTotalDigits, self.decimalEdit.totalDigits)
        setValue(self.dceFractionDigits, self.decimalEdit.fractionDigits)
        setValue(self.dceNonNegative, self.decimalEdit.nonNegative)
        setValue(self.dceSeparateThousands, self.decimalEdit.separateThousands)
