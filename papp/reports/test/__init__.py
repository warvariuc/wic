"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import os, sys
from PyQt4 import QtCore, QtGui

from wic.forms import WForm, setValue, getValue
from datetime import date as Date
from dateutil.relativedelta import relativedelta as RelDelta
import papp


class Form(WForm):

    _iconPath = ':/icons/fugue/leaf-wormhole.png'
    _formTitle = 'Тестовые модуль и форма'

    def onOpen(self): # called by the system after it loads the Form
        print('Форма загружена.')

        self._.dteShowSelector = self.dateEdit.isSelectorVisible()
        self._.dateEdit = Date.today()
        self._.decimalEdit = '20000000.1251'
        self.updateInfoAboutDecimalEdit()

    def onClose(self): # Form is asked to be closed
#        if QtGui.QMessageBox.question(self, 'Подтверждение', 'Вы действительно хотите закрыть форму?',
#                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
#            return False
        print('Форма закрывается.')

    def on_dceShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.selectorVisible = state
        self.decimalEdit.setFocus()

    def on_dceNonNegative_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.nonNegative = state

    def on_dceSeparateThousands_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.thousandsSeparated = state

    def on_decimalEdit_edited(self):
        print('WDecimalEdit отредактирован. Новое значение: %s' % self._.decimalEdit)

    def on_dteShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.dateEdit.selectorVisible = state

    def on_dateEdit_edited(self):
        print('WDateEdit отредактирован. Новое значение: %s' % self._.dateEdit)

    @QtCore.pyqtSlot()
    def on_testGm_clicked(self):
        papp.test()

    def on_dceTotalDigits_valueChanged(self, text):
        self.decimalEdit.setMaxDigits(int(text))
        self.updateInfoAboutDecimalEdit()

    def on_dceFractionDigits_valueChanged(self, text):
        self.decimalEdit.setFractionDigits(int(text))
        self.updateInfoAboutDecimalEdit()

    def updateInfoAboutDecimalEdit(self):
        self._.dceShowSelector = self.decimalEdit.selectorVisible
        self._.dceTotalDigits = self.decimalEdit.maxDigits
        self._.dceFractionDigits = self.decimalEdit.fractionDigits
        self._.dceNonNegative = self.decimalEdit.nonNegative
        self._.dceSeparateThousands = self.decimalEdit.thousandsSeparated
