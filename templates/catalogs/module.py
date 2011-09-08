from PyQt4 import QtCore, QtGui

def on_Module_load() : # event called by m_py after it loads module
    return True # аналог СтатусВозврата (1) в 1С

def on_Form_load() : # event called by m_py after it loads Form
    pass

def on_Form_close() : # Form is asked to be closed
    pass
