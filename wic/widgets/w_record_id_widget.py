from PyQt4 import QtGui, QtCore


class WCatalogItemIdWidget(QtGui.QLineEdit):
    """Custom widget - for keeping id of a record."""

    changed = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        #self.setAlignment(QtCore.Qt.AlignRight)
        self.setReadOnly(True)
        self.selector = QtGui.QToolButton(self)
        self.selector.setIcon(QtGui.QIcon(':/icons/fugue/cards-stack.png'))
        self.selector.setCursor(QtCore.Qt.PointingHandCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selector.clicked.connect(self.openRecordList)

        self._db = None
        self.setModel('') # will cause text update
        
        self.setSelectorVisible(True) # cause style recalculation

    def getDb(self):
        return self._db
    def setDb(self, db):
        import orm
        assert isinstance(db, orm.GenericAdapter), 'db argument must be a GenericAdapter.'
        self._db = db
    db = QtCore.pyqtProperty(str, getDb, setDb)

    def getModel(self):
        return self._model
    def setModel(self, model):
        assert isinstance(model, str), 'Model path must be a string'
        self._model = model
        self.setId(None)
    model = QtCore.pyqtProperty(str, getModel, setModel)

    def getId(self):
        return self._id
    def setId(self, id):
        assert id is None or isinstance(id, int), 'id must be an int or None (%s)' % id
        self._id = id
        self.changed.emit()
        self._format() # to reflect changes
    id = QtCore.pyqtProperty(int, getId, setId)

    def clear(self):
        self.setId(None)

    def _format(self):
        self.setText('' if self._id is None else str(self._id))

    def resizeEvent(self, event):
        sz = self.selector.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.selector.move(self.rect().right() - frameWidth - sz.width(),
                      (self.rect().bottom() + 1 - sz.height()) / 2)

    def _updateStyle(self):
        borderWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth) + 1
        selectorWidth = self.selector.sizeHint().width() if self.isSelectorVisible() else 0
        self.setStyleSheet('QLineEdit { padding-right: %dpx; }' % (selectorWidth + borderWidth))
#        fm = QtGui.QFontMetrics(self.font()) # font metrics
#        maxText = '9' * self._maxDigits + '. '
#        self.setMinimumSize(fm.width(maxText) + selectorWidth + borderWidth * 2,
#                   max(fm.height(), self.selector.sizeHint().height() + borderWidth * 2))

    def isSelectorVisible(self):
        return not self.selector.isHidden()
    def setSelectorVisible(self, value):
        self.selector.setVisible(value)
        self._updateStyle()
    selectorVisible = QtCore.pyqtProperty(bool, isSelectorVisible, setSelectorVisible)

    def mouseDoubleClickEvent(self, mouseEvent):
        if mouseEvent.button() == QtCore.Qt.LeftButton:
            #self.selectAll() # select all on double click, otherwise only group of characters will be selected
            self.openRecord()

    def keyPressEvent(self, keyEvent):
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            key = keyEvent.key()
            if key == QtCore.Qt.Key_Insert:
                self.openRecordList()
                return
            elif key == QtCore.Qt.Key_Delete:
                self.clear()
                return
            elif key == QtCore.Qt.Key_Space:
                self.openRecord()
                return
        super().keyPressEvent(keyEvent)

    def openRecord(self):
        """"""
        if self._db:
            import orm
            from wic import forms
            model = orm.getObjectByPath(self._model)
            catalogItem = model.getOneById(self._db, self._id)
            forms.openCatalogItemForm(catalogItem)

    def openRecordList(self):
        """"""
        #from wic import forms
        #WPopupCalculator(self).show()

    def contextMenuEvent(self, qContextMenuEvent):
        menu = getattr(self, 'menu', None)
        if not menu:
            from wic.menu import createAction, addActionsToMenu
            menu = QtGui.QMenu(self) # context menu
            addActionsToMenu(menu, (
                createAction(menu, 'Select', self.openRecordList, 'Insert', ':/icons/fugue/cards-stack.png'),
                createAction(menu, 'Open', self.openRecord, 'Space', ':/icons/fugue/card-address.png'),
                createAction(menu, 'Clear', self.clear, 'Delete', ':/icons/fugue/eraser.png'),
            ))
            self.menu = menu
        menu.popup(qContextMenuEvent.globalPos())


if __name__ == '__main__': # some tests
    app = QtGui.QApplication([])
    widget = WRecordIdWidget(None)
    widget.show()
    app.exec()
