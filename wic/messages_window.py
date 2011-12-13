from PyQt4 import QtCore, QtGui

class MessagesWindow(QtGui.QDockWidget):
    def __init__(self,  mainWindow):
        super().__init__('Messages', mainWindow)

        self.setObjectName('messagesWindowDock')
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        
        self.textEdit = QtGui.QTextEdit(self)
        self.textEdit.setAcceptRichText(False)
        self.textEdit.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.textEdit.setReadOnly(True)
        self.textEdit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.textEdit.customContextMenuRequested.connect(self.showContextMenu)

        self.setWidget(self.textEdit)

    def showContextMenu(self, coord):
        if not hasattr(self, 'menu'): # create the context menu for Message Window
            self.menu = QtGui.QMenu(self.textEdit)
            self.menu.addAction('Clear', self.textEdit.clear)
            self.menu.addAction('Copy', self.textEdit.copy, QtGui.QKeySequence.Copy)
            self.menu.addAction('Select all', self.textEdit.selectAll, QtGui.QKeySequence.SelectAll)

        self.menu.popup(self.textEdit.mapToGlobal(coord))

    def printMessage(self, txt, showDateTime= False, autoPopup= True, end= '\n'):
        tc = self.textEdit.textCursor()
        tc.movePosition(QtGui.QTextCursor.End)
        self.textEdit.setTextCursor(tc)
        if showDateTime: 
            txt = QtCore.QDateTime.currentDateTime().toString('yyyy/MM/dd hh:mm:ss ') + txt
        self.textEdit.insertHtml(('%s%s' % (txt, end)).replace('\n', '<br>'))
        self.textEdit.ensureCursorVisible() # scroll to the new message
        if autoPopup: 
            self.show()
