import os, sys
from PyQt4 import QtCore, QtGui, uic

from wic import w
from wic.form import WForm
from wic.widgets.w_date import Date
import conf as gM


class Form(WForm):
    ''''''
#    @QtCore.pyqtSlot()
#    def on_pushButton_clicked(self):
#        # Using the same logic this slot is connected to the 'working' button
#        # and only called once. The reason for this is that a lot of Qt signals
#        # are overloaded, and if you dont specify which specific variant you
#        # are interested in, then _all_ of them will be connected. Once way to
#        # specify the specific signal is by use of the decorator above - in
#        # this case, we will be connected to the signal with no arguments
#        #
#        # It is better explained in the documentation:
#        # http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/pyqt4ref.html#connecting-slots-by-name
#        print('!!!')

    def on_dceShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.showSelector = state
        self.decimalEdit.setFocus()
    
    def on_dceNonNegative_stateChanged(self, state): # widget 'checkBox' emited signal
        w.printMessage('on_dceNonNegative_stateChanged')
        self.decimalEdit.nonNegative = state

    def on_dceSeparateThousands_stateChanged(self, state): # widget 'checkBox' emited signal
        self.decimalEdit.separateThousands = state
    
    def on_decimalEdit_edited(self):
        w.printMessage('WDecimalEdit отредактирован. Новое значение: ' + self.decimalEdit.valueStr())

    def on_dteShowSelector_stateChanged(self, state): # widget 'checkBox' emited signal
        self.dateEdit.showSelector = state

    def on_dateEdit_edited(self):
        w.printMessage('WDateEdit отредактирован. Новое значение: %s' % self.dateEdit.value)

    @QtCore.pyqtSlot()
    def on_testGm_clicked(self):
        gM.test()

    def on_open(self): # event called by wic after it loads Form
        w.printMessage ('Форма загружена.')
        self.setWindowTitle("Тестовые модуль и форма")
        #self.parentWidget().setWindowIcon(QtGui.QIcon(":/icons/fugue/calculator.png"))
        self.setWindowIcon(QtGui.QIcon(":/icons/fugue/calculator.png"))
        #self.parentWidget().setWindowState (Qt.WindowMaximized)
        self.dteShowSelector.setChecked(self.dateEdit.showSelector)
#        widgets.dateEdit = Date.today()
#        widgets.decimalEdit = '20000000000.1251'
#        updateInfoAboutDecimalEdit()

    def on_close(self): # Form is asked to be closed
        if QtGui.QMessageBox.question(self, 'Подтверждение', 'Вы действительно хотите закрыть форму?', 
                        QtGui.QMessageBox.Yes, QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
            return False
        w.printMessage('Форма закрывается.')

def updateInfoAboutDecimalEdit():
    widgets.dceShowSelector = form.decimalEdit.showSelector
    widgets.dceTotalDigits = form.decimalEdit.totalDigits
    widgets.dceFractionDigits = form.decimalEdit.fractionDigits
    widgets.dceNonNegative = form.decimalEdit.nonNegative
    widgets.dceSeparateThousands = form.decimalEdit.separateThousands

def dceTotalDigits_valueChanged(i):
    form.decimalEdit.totalDigits = i
    updateInfoAboutDecimalEdit()

def dceFractionDigits_valueChanged(i):
    form.decimalEdit.fractionDigits = i
    updateInfoAboutDecimalEdit()








#todo сделать объект Справочник - буфер между базой данных и формой. будет содержать метод ЗагрузитьДанныеВФорму(), БлокировкаЗаписи (0/1), Записать(), Новый(), Найти(Код) - аналог объект Справочник из 1С
# форма будет ссылаться на этот объект
# каким образом узнать какого вида объект БД к к-му привязана форма?
# will contain info about fields and indexes
    