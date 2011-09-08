from PyQt4 import QtCore, QtGui

class MessagesWindow(QtCore.QObject):
    def __init__(self,  main_window):
        super().__init__(main_window)

        self.main_window = main_window
        self.dockWidget = QtGui.QDockWidget('Окно сообщений', main_window) # main_window now has to children: dock and messages window ? is this correct?
        self.dockWidget.setObjectName('messagesWindowDock')
        self.dockWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.text_edit = QtGui.QTextEdit(self.dockWidget)
        self.dockWidget.setWidget(self.text_edit)
        
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.text_edit.setReadOnly(True)

        self.text_edit.setContextMenuPolicy (QtCore.Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect (self.show_context_menu)

    def show_context_menu(self, coord):
        if not hasattr(self, "menu"): # create the context menu for Message Window
            self.menu = QtGui.QMenu(self.text_edit)
            self.menu.addAction('Очистить', self.text_edit.clear)
            self.menu.addAction('Запомнить', self.text_edit.copy, QtGui.QKeySequence.Copy)
            self.menu.addAction('Выделить всё', self.text_edit.selectAll, QtGui.QKeySequence.SelectAll)

        self.menu.popup(self.text_edit.mapToGlobal(coord))

    def printMessage(self, txt, showDateTime=False, autoPopup=True):
        tc = self.text_edit.textCursor()
        tc.movePosition(QtGui.QTextCursor.End)
        self.text_edit.setTextCursor(tc)
        if showDateTime: txt = QtCore.QDateTime.currentDateTime().toString('yyyy/MM/dd hh:mm:ss ') + txt
        self.text_edit.insertHtml((str(txt) + '\n').replace('\n', '<br>'))
        self.text_edit.ensureCursorVisible()
        if autoPopup: self.dockWidget.show()
