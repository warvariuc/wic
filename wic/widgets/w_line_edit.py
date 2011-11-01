from PyQt4 import QtGui, QtCore

class WLineEdit(QtGui.QLineEdit): # http://labs.qt.nokia.com/2007/06/06/lineedit-with-a-clear-button/
    def __init__(self, parent = None):
        super().__init__(parent)
    
        self.clearButton = QtGui.QToolButton(self)
        pixmap = QtGui.QPixmap(':/icons/fugue/cross-white.png')
        self.clearButton.setIcon(QtGui.QIcon(pixmap))
        self.clearButton.setIconSize(pixmap.size())
        self.clearButton.setCursor(QtCore.Qt.ArrowCursor)
        self.clearButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self.clearButton.hide()
        self.clearButton.clicked.connect(self.clear)
        self.textChanged.connect(self.updateCloseButton)
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet('QLineEdit { padding-right: %spx; } ' % str(self.clearButton.sizeHint().width() + frameWidth + 1))
        #self.setStyleSheet('QLineEdit { margin-right: %spx; } ' % str(self.clearButton.sizeHint().width() + frameWidth + 1))
        msz = self.minimumSizeHint()
        self.setMinimumSize(max(msz.width(), self.clearButton.sizeHint().height() + frameWidth * 2 + 2),
                   max(msz.height(), self.clearButton.sizeHint().height() + frameWidth * 2 + 2))


    def resizeEvent(self, event):
        sz = self.clearButton.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.clearButton.move(self.rect().right() - frameWidth - sz.width(),
                      (self.rect().bottom() + 1 - sz.height())/2)

    def updateCloseButton(self, text):
        self.clearButton.setVisible(bool(text))

 

if __name__ == '__main__': # some tests
    import sys
    app = QtGui.QApplication(sys.argv)
    m = WLineEdit(None)
    m.show()
    app.exec()
