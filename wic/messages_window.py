from PyQt4 import QtCore, QtGui

class MessagesWindow(QtCore.QObject):
    def __init__(self,  mainWindow):
        super().__init__(mainWindow)

        self.mainWindow = mainWindow
        self.dockWidget = QtGui.QDockWidget('Окно сообщений', mainWindow) # main_window now has two children: dock and messages window ? is this correct?
        self.dockWidget.setObjectName('messagesWindowDock')
        self.dockWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.textEdit = QtGui.QTextEdit(self.dockWidget)
        self.dockWidget.setWidget(self.textEdit)

        self.textEdit.setAcceptRichText(False)
        self.textEdit.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.textEdit.setReadOnly(True)

        self.textEdit.setContextMenuPolicy (QtCore.Qt.CustomContextMenu)
        self.textEdit.customContextMenuRequested.connect (self.showContextMenu)

    def showContextMenu(self, coord):
        if not hasattr(self, "menu"): # create the context menu for Message Window
            self.menu = QtGui.QMenu(self.text_edit)
            self.menu.addAction('Очистить', self.text_edit.clear)
            self.menu.addAction('Запомнить', self.text_edit.copy, QtGui.QKeySequence.Copy)
            self.menu.addAction('Выделить всё', self.text_edit.selectAll, QtGui.QKeySequence.SelectAll)

        self.menu.popup(self.text_edit.mapToGlobal(coord))

    def printMessage(self, txt, showDateTime=False, autoPopup=True):
        tc = self.textEdit.textCursor()
        tc.movePosition(QtGui.QTextCursor.End)
        self.textEdit.setTextCursor(tc)
        if showDateTime: txt = QtCore.QDateTime.currentDateTime().toString('yyyy/MM/dd hh:mm:ss ') + txt
        self.textEdit.insertHtml((str(txt) + '\n').replace('\n', '<br>'))
        self.textEdit.ensureCursorVisible()
        if autoPopup: self.dockWidget.show()
