"""
Этот модуль содержит основные классы и функции для работы пользовательских модулей.
Его следует импортировать, когда главные компоненты системы уже загружены, поскольку он их использует.
"""

import os, sys
from types import ModuleType
import yaml, subprocess, datetime
from PyQt4 import QtGui
import wic

#shortcuts
appDir = wic.appDir # этот модуль должен загружаться после всех основных модулей
confDir = '' # будет заполнена при загрузке конфигурации
mainWindow = wic.mainWindow
statusBar = mainWindow.statusBar()
printMessage = mainWindow.messagesWindow.printMessage
globalModule = None



        
def execFunc(funcName, obj, **kwargs):
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
        with open(lockFilePath, 'w', encoding= 'utf8') as file:
            file.write(str(datetime.datetime.today()))
    global confDir
    confDir = _confDir
    QtGui.qApp.confDir = _confDir
    loadGlobalModule(os.path.join(QtGui.qApp.confDir, 'global_module.py'))


import errno

def pid_exists(pid):
    '''Verify if process with given pid is running (on this machine).'''
    try:
        os.kill(pid, 0)
    except OSError as exc:
        return exc.errno == errno.EPERM
    else:
        return True