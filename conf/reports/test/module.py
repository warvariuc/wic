# form - Form attached to the module
# db_catalog, db_document, db_account, etc. - object responsible for connection between this module, Form and database record
from PyQt4 import QtCore, QtGui
import w
from w_date import Date
import gM

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

def dceShowSelector_stateChanged(_state): # widget 'checkBox' emited signal
    form.decimalEdit.showSelector = _state
    form.decimalEdit.setFocus()

def dceNonNegative_stateChanged(_state): # widget 'checkBox' emited signal
    form.decimalEdit.nonNegative = _state

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
