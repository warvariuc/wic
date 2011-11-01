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




def loadModule(filePath):
        filePath = str(filePath)
                
        try:
            module = ModuleType('form_module')
            module.__file__ = filePath
#            module.QtGui = QtGui
            #module.__dict__.update(PyQt4.QtCore.__dict__)
            with open(filePath, 'r', encoding='utf8') as f:
                exec(f.read(), module.__dict__)
        except:
            printMessage('<b>Ошибка при загрузке пользовательского модуля: </b>' + filePath)
            raise
        
        res = execFunc('module_loaded', module)
        if res == False: return # предопределнная процедура вернула False - отменить дальнейшую загрузку модуля
        
        if isinstance(res, type) and issubclass(res, QtGui.QDialog): # предопределенная процедура вернула свой базовый класс формы для использования, т.е. не искать предопределенную форму в той же директории
            formClass = res
        else: # загрузить класс формы с диска - в той же директории, что и модуль
            if isinstance(res, str): # предопределенная процедура вернула свое имя файла с формой в директории модуля
                if os.path.isabs(res): # указан абсолютный путь
                    uiFilePath = res
                else:
                    uiFilePath = os.path.join(os.path.dirname(filePath), res)
            else:
                uiFilePath = os.path.join(os.path.dirname(filePath), 'form.ui')
            formClass, formBaseClass = uic.loadUiType(uiFilePath)
            if not issubclass(formBaseClass, QtGui.QDialog):
                printMessage('<b>Форма не загружена - ожидается QDialog: </b>' + uiFilePath)
                return
            
        class WFormClass(formClass, QtGui.QDialog):
            def __init__(self, parent, module):
                super().__init__(parent)
                self.setupUi(self)
                self.finished.connect(self.close)
                self.module = module
                module.form = self # set reference to the form
                self.bindSignals()
            
            def closeEvent(self, event):
                if execFunc('form_aboutToClose', self.module) == False: # вызов предопределенной процедуры
                    event.ignore()
                    self.show()
                    return
                self.parentWidget().close() # close sub window

            def bindSignals(self):
                'Связать стандартные сигналы стандартных виджетов формы к предопределенным процедурам модуля.'
                for child in self.children():
                    childName = child.objectName()

                    def bind(signalName):
                        try:
                            getattr(child, signalName).connect(getattr(self.module, childName+'_'+signalName))
                        except Exception as err:
                            err #print('Binding signals notice: %s\n' % str(err))

                    if isinstance(child, QtGui.QTextEdit): bind('textChanged')
                    elif isinstance(child, QtGui.QCheckBox): bind('stateChanged')
                    elif isinstance(child, (WDateEdit, WDecimalEdit)): bind('edited') # check this classes before QLineEdit, because they are its descendants
                    elif isinstance(child, QtGui.QLineEdit): bind('textEdited')
                    elif isinstance(child, QtGui.QPushButton): bind('clicked')
                    elif isinstance(child, QtGui.QSpinBox): bind('valueChanged')



        #uiFilename = os.path.join(os.path.dirname(filePath), 'form.ui')
        #form = uic.loadUi(uiFilename, WFormClass(None)) # create form
        form = WFormClass(None, module) # create form
        window = mainWindow.mdiArea.addSubWindow(form) # create subwindow with the form
        window.show()
        module.widgets = WFormWidgetHooker(form) # helper for the form
        execFunc('form_loaded', module) # предопределенная процедура
        
        

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


def putToForm(data, uiFilePath, dialog):
    'Загрузить форму с диска, заполнить поля данными data и вернуть форму'
    dialog = uic.loadUi(uiFilePath, QtGui.QDialog(dialog))
    for name, value in data.items():
        try: widget = getattr(dialog, name) # ищем нужный атрибут на форме
        except AttributeError: continue # такого нет
        if isinstance(widget, QtGui.QLineEdit):
            widget.setText(value)
            widget.home(False)
        elif isinstance(widget, QtGui.QPlainTextEdit):
            widget.setPlainText(value)
        elif isinstance(widget, QtGui.QLabel):
            widget.setText(value)
        elif isinstance(widget, QtGui.QComboBox):
            lineEdit = widget.lineEdit()
            if lineEdit: #Only editable combo boxes have a line edit
                lineEdit.setText(value)
        elif isinstance(widget, QtGui.QSpinBox):
            widget.setValue(int(value))
        elif isinstance(widget, QtGui.QCheckBox):
            widget.setChecked(value)
    return dialog


def getFromForm(dialog):
    data = {}
    for widget in dialog.children():
        value = None
        if isinstance(widget, QtGui.QLineEdit):
            value = widget.text()
        elif isinstance(widget, QtGui.QPlainTextEdit):
            value = widget.toPlainText()
        elif isinstance(widget, QtGui.QComboBox):
            lineEdit = widget.lineEdit()
            if lineEdit: #Only editable combo boxes have a line edit
                value = lineEdit.text()
        elif isinstance(widget, QtGui.QSpinBox):
            value = widget.value()
        elif isinstance(widget, QtGui.QCheckBox):
            value = bool(widget.isChecked())
        if value is not None:
            data[widget.objectName()] = value
    return data


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

