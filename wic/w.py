"""
Этот модуль содержит основные классы и функции для работы пользовательских модулей.
Его следует импортировать, когда главные компоненты системы уже загружены, поскольку он их использует.
"""

import os, sys
from types import ModuleType
from PyQt4 import QtGui, uic
from wic.widgets.w_date_edit import WDateEdit
from wic.widgets.w_decimal_edit import WDecimalEdit
import yaml, subprocess, datetime

#shortcuts
appDir = QtGui.qApp.appDir # этот модуль должен загружаться после всех основных модулей
confDir = '' # будет заполнена при загрузке конфигурации
mainWindow = QtGui.qApp.mainWindow
statusBar = mainWindow.statusBar()
printMessage = mainWindow.messagesWindow.printMessage
globalModule = None



class WFormWidgetHooker():
    '''Перехватчик виджетов формы. При попытке обращения к стандартным виджетам, класс возвращает/устанавливает значение, а не ссылку.
    Т.е. вместо form.checkBox.setChecked(True), можно писать widget.checkBox = True или widget['checkBox'] = True.
    Таким же образом, вместо txt = form.lineEdit.text(), можно писать txt = widget.lineEdit или txt = widget['lineEdit'].
    Если же требуется работа именно с виджетом, а не с его значением, используйте form.'''
    def __init__(self, form):
        super().__setattr__('form', form) # to bypass overriden __setattr__
        
    def __setattr__(self, name, value):
        try:
            widget = getattr(self.form, name)
        except AttributeError:
            raise AttributeError('The hooked form doesn\'t have attribute ' + name)

        if isinstance(widget, QtGui.QTextEdit): widget.setPlainText(value)
        elif isinstance(widget, QtGui.QCheckBox): 
            widget.blockSignals(True) # http://stackoverflow.com/questions/1856544/qcheckbox-is-it-really-not-possible-to-differentiate-between-user-induced-change
            widget.setChecked(value)
            widget.blockSignals(False) 
        elif isinstance(widget, (WDateEdit, WDecimalEdit, QtGui.QSpinBox)): widget.setValue(value)
        elif isinstance(widget, (QtGui.QLineEdit, QtGui.QPushButton)): widget.setText(value)

    def __getattr__(self, name):
        try:
            widget = getattr(self.form, name)
        except AttributeError:
            raise AttributeError('The hooked form does not have attribute ' + name)
    
        if isinstance(widget, QtGui.QTextEdit): return widget.plainText()
        elif isinstance(widget, QtGui.QCheckBox): return widget.isChecked()
        elif isinstance(widget, (WDateEdit, WDecimalEdit)): return widget.value
        elif isinstance(widget, QtGui.QSpinBox): return widget.value()
        elif isinstance(widget, (QtGui.QLineEdit, QtGui.QPushButton)): return widget.text()

    def __getitem__(self, name):
        return self.__getattr__(name)

    def __setitem__(self, name, value):
        self.__setattr__(name, value)





        
        

def execFunc(funcName, obj,  **kwargs):
    'Выполнить функцию объекта (обычно, это предопределенная процедура пользовательского модуля).'
    try: func = getattr(obj, funcName)
    except AttributeError: return None
    else:
        if not hasattr(func, "__call__"): # is it callable?
            return None  
    return func(**kwargs) # == False else True #для того, чтобы None результат (когда функция ничего не возвращает) не воспринмался как False проверящими условие функциями


def requestExit():
    'Вызвать предопределенную процедуру глобального модуля при попытке выхода из системы.'
    return execFunc("system_aboutToExit", globalModule) # был СтатусВозврата (0) # предопределенная процедура


def loadGlobalModule(pathFile):
    'Загрузить глобальный модуль, к-й находится по указанному пути.'
    __import__('db_info').createConnection() # creates default connection for the application
    global globalModule
    globalModule = ModuleType('gM')
    with open(pathFile, 'r', encoding='utf8') as f:
        exec(f.read(), globalModule.__dict__)
    sys.modules['gM'] = globalModule
    if execFunc("system_started", globalModule) == False: # был СтатусВозврата (0) # предопределенная процедура
        return


def loadFromFile(filePath):
    'Загрузить данные из указанного yaml файла и вернуть их в виде словаря.'
    if not os.path.isfile(filePath):
        printMessage('YAML файл не найден: ' + filePath)
        return None# specified configuration file doesn't exist
    with open(filePath, encoding='utf8') as file:
        data = yaml.load(file)
    return data


def saveToFile(data, filePath):
    'Записать данные из словаря data в указанный yaml файл.'
    with open(filePath, 'w', encoding='utf8') as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
    #print(yaml.dump(data, allow_unicode=True, default_flow_style=False))




def editForm(filePath):
    'Редактировать форму по указанному пути - открыть редактор форм.'
    if not os.path.isfile(filePath): #file doesn't exist
        printMessage('Файл формы не найден: ' + filePath)
    os.putenv('PYQTDESIGNERPATH', os.path.join(QtGui.qApp.appDir, 'widgets'))
    os.putenv('PATH', os.getenv('PATH', '') + ';' + os.path.dirname(sys.executable)) #designer needs python.dll to use python based widgets. on windows the dll is not in system32
    params = ['designer', filePath]
    subprocess.Popen(params)


def editModule(filePath):
    'Редактировать модуль по указанному пути - открыть редактор исходного кода.'
    if not os.path.isfile(filePath): #file doesn't exist
        printMessage('Файл модуля не найден: ' + filePath)
        return 
    params = [sys.executable, os.path.join(os.path.dirname(sys.executable), 'Lib', 'idlelib', 'idle.pyw' ), '-e', filePath] # http://docs.python.org/library/idle.html#command-line-usage
    subprocess.Popen(params)



def loadConf(_confDir):
    'Загрузить конфигурацию, находящуюся по указанному пути'
    lockFilePath = os.path.join(_confDir, 'lock')
    if False: #os.path.exists(lockFilePath):
        QtGui.QMessageBox.warning(mainWindow, 'Конфигурация заблокирована', 
                'Директория конфигурации заблокирована.')
        return
    else:
        with open(lockFilePath, 'w', encoding='utf8') as file:
            file.write(str(datetime.datetime.today()))
    global confDir
    confDir = _confDir
    QtGui.qApp.confDir = _confDir
    loadGlobalModule(os.path.join(QtGui.qApp.confDir, 'global_module.py'))

