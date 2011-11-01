'This is a user module with configurator code for wic platform'
from PyQt4 import QtGui
import sys, os
import w


class FormClass(QtGui.QDialog):
    def setupUi(self, Dialog):
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setMargin(0)
        Dialog.setWindowTitle('Дизайнер конфигурации')

def module_loaded():
    return FormClass

def form_loaded(): # предопределенная процедура, аналог ПослеОткрытия ФормЕкс
    form.parent().setWindowIcon(QtGui.QIcon(':/icons/fugue/block.png'))
    
    global menu
    menu = QtGui.QMenu('Конфигурация', form)
    menu.addAction(QtGui.QIcon(':/icons/fugue/database--pencil.png'), 'Обновить структуру БД')
    menu.addSeparator()
    menu.addAction(QtGui.QIcon(':/icons/fugue/cross-white.png'), 'Закрыть конфигуратор', form.close)
    #w.mainWindow.menuBar().addMenu(menu)
    w.mainWindow.menuBar().insertMenu(w.mainWindow.serviceMenu.menuAction(), menu)
    
    cfgTreeView = __import__('cfg_tree_view').CfgTreeView(form)
    form.verticalLayout.addWidget(cfgTreeView)
    

