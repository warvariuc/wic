from PyQt5 import QtGui, QtCore, QtWidgets


class LineEdit(QtWidgets.QLineEdit):
    # http://labs.qt.nokia.com/2007/06/06/lineedit-with-a-clear-button/
    def __init__(self, parent= None):
        super().__init__(parent)
    
        self.clear_button = QtWidgets.QToolButton(self)
        pixmap = QtGui.QPixmap(':/icons/fugue/cross-white.png')
        self.clear_button.setIcon(QtGui.QIcon(pixmap))
        self.clear_button.setIconSize(pixmap.size())
        self.clear_button.setCursor(QtCore.Qt.ArrowCursor)
        self.clear_button.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        self.clear_button.hide()
        self.clear_button.clicked.connect(self.clear)
        self.textChanged.connect(self.updateCloseButton)
        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet('QLineEdit { padding-right: %spx; } ' %
                           str(self.clear_button.sizeHint().width() + frameWidth + 1))
        msz = self.minimumSizeHint()
        self.setMinimumSize(
            max(msz.width(), self.clear_button.sizeHint().height() + frameWidth * 2 + 2),
            max(msz.height(), self.clear_button.sizeHint().height() + frameWidth * 2 + 2))


    def resizeEvent(self, event):
        sz = self.clear_button.sizeHint()
        frame_width = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        self.clear_button.move(self.rect().right() - frame_width - sz.width(),
                               (self.rect().bottom() + 1 - sz.height()) / 2)

    def updateCloseButton(self, text):
        self.clear_button.setVisible(bool(text))

 
def test():
    import widgets_rc
    app = QtWidgets.QApplication([])
    w = LineEdit(None)
    w.show()
    app.exec()


if __name__ == '__main__':
    test()
