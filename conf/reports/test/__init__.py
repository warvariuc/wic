import os, sys
from PyQt4 import QtCore, QtGui, uic

from wic import w
from wic import w_form
from wic.widgets.w_date import Date
from conf import global_module as gM


class Form(w_form.WForm):
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
    def dceShowSelector_stateChanged(self, _state): # widget 'checkBox' emited signal
        self.decimalEdit.showSelector = _state
        self.decimalEdit.setFocus()
    
    def dceNonNegative_stateChanged(self, _state): # widget 'checkBox' emited signal
        self.decimalEdit.nonNegative = _state



def module_loaded(): # event called by m_py after it loads module
    w.printMessage ('Модуль загружен.')
    return True # аналог СтатусВозврата (1) в 1С

def form_loaded(): # event called by m_py after it loads Form
    w.printMessage ('Форма загружена.')
    form.setWindowTitle("Тестовые модуль и форма")
    form.parent().setWindowIcon(QtGui.QIcon(":/icons/fugue/calculator.png"))
    #Form.parentWidget().setWindowState (Qt.WindowMaximized)
    widgets.dateEdit = Date.today()
    widgets.decimalEdit = '20000000000.1251'
    updateInfoAboutDecimalEdit()
    form.dteShowSelector.setChecked(form.dateEdit.showSelector)

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


def dceSeparateThousands_stateChanged(_state): # widget 'checkBox' emited signal
    form.decimalEdit.separateThousands = _state

def decimalEdit_edited():
    w.printMessage('WDecimalEdit отредактирован. Новое значение: ' + form.decimalEdit.valueStr())


def dteShowSelector_stateChanged(_state): # widget 'checkBox' emited signal
    form.dateEdit.showSelector = _state
    # if _state:
        # form.label.setPixmap(QtGui.QPixmap(":/newPrefix/icons/calendar-blue.png"))
    # else:
        # form.label.setPixmap(QtGui.QPixmap())

def dateEdit_edited():
    w.printMessage('WDateEdit отредактирован. Новое значение: ' + str(form.dateEdit.value))

def testGm_clicked(_checked = False): # widget 'checkBox' emited signal
    gM.test()

def Close_clicked(_checked = False): # widget 'checkBox' emited signal
    form.close()

def form_aboutToClose(): # Form is asked to be closed
    if QtGui.QMessageBox.question(form, 'Подтверждение',
                'Вы действительно хотите закрыть форму?', QtGui.QMessageBox.Yes, QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
        return False
    w.printMessage('Форма закрывается.')

#todo сделать объект Справочник - буфер между базой данных и формой. будет содержать метод ЗагрузитьДанныеВФорму(), БлокировкаЗаписи (0/1), Записать(), Новый(), Найти(Код) - аналог объект Справочник из 1С
# форма будет ссылаться на этот объект
# каким образом узнать какого вида объект БД к к-му привязана форма?
# will contain info about fields and indexes
    