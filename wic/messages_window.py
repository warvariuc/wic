from PyQt5 import QtCore, QtGui, QtWidgets
from wic.datetime import DateTime
from wic import menus


class MessagesWindow(QtWidgets.QDockWidget):
    def __init__(self, mainWindow):
        super().__init__('Messages', mainWindow)

        self.setObjectName('messagesWindowDock')
        self.setFocusPolicy(QtCore.Qt.NoFocus)

        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setAcceptRichText(False)
        self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)
        self.textEdit.setReadOnly(True)
        self.textEdit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.textEdit.customContextMenuRequested.connect(self.showContextMenu)

        self.setWidget(self.textEdit)

    def showContextMenu(self, coord):
        if not hasattr(self, 'menu'): # create the context menu for Message Window
            self.menu = QtWidgets.QMenu(self.textEdit)
            menus.addActionsToMenu(self.menu, (
                menus.createAction(self.textEdit, 'Clear', self.textEdit.clear, icon = ':/icons/fugue/eraser.png'),
                menus.createAction(self.textEdit, 'Copy', self.textEdit.copy, QtGui.QKeySequence.Copy, ':/icons/fugue/document-copy.png'),
                menus.createAction(self.textEdit, 'Select all', self.textEdit.selectAll, QtGui.QKeySequence.SelectAll, ':/icons/fugue/selection-select.png'),
            ))
        self.menu.popup(self.textEdit.mapToGlobal(coord))

    def printMessage(self, txt, showDateTime = False, autoPopup = True, end = '\n'):
        if txt == ' ':
            txt = '&nbsp;'
        else:
            txt = ('%s%s' % (txt, end)).replace('\n', '<br>')
            if showDateTime:
                txt = '%s %s' % (DateTime.now().strftime('%Y-%m-%d %H:%M:%S'), txt)
        tc = self.textEdit.textCursor()
        tc.movePosition(QtGui.QTextCursor.End)
        self.textEdit.setTextCursor(tc)
        self.textEdit.insertHtml(txt)
        self.textEdit.ensureCursorVisible() # scroll to the new message
#        if autoPopup:
#            self.show()
        self.setVisible(autoPopup)
