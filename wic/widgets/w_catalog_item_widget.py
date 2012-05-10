from PyQt4 import QtGui, QtCore


class WCatalogItemWidget(QtGui.QLineEdit):
    """Custom widget - for keeping a catalog item."""

    changed = QtCore.pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.selector = QtGui.QToolButton(self)
        self.selector.setIcon(QtGui.QIcon(':/icons/fugue/cards-stack.png'))
        self.selector.setCursor(QtCore.Qt.PointingHandCursor)
        self.selector.setStyleSheet('QToolButton { border: none; padding: 0px; }')
        self.selector.setFocusPolicy(QtCore.Qt.NoFocus)
        self.selector.clicked.connect(self.selectItem)

        self.setModel('') # will cause text update
        self._db = None
        self._item = None

        self.setSelectorVisible(True) # cause style recalculation

    def getDb(self):
        return self._db
    def setDb(self, db):
        import orm
        assert isinstance(db, orm.GenericAdapter), 'db argument must be a GenericAdapter.'
        self._db = db

    def getModel(self):
        return self._model
    def setModel(self, model):
        assert isinstance(model, str), 'Model path must be a string'
        self._model = model
        if isinstance(self._item, model):
            self.setItem(None) # remove item is it's not the same model as the set model
    model = QtCore.pyqtProperty(str, getModel, setModel)

    def getItem(self):
        return self._id
    def setItem(self, item):
        assert id is None or isinstance(id, int), 'id must be an int or None (%s)' % id
        self._id = id
        self.changed.emit()
        self._format() # to reflect changes

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
        backColor = hex(QtGui.QApplication.palette().alternateBase().color().rgb())[4:]
        self.setStyleSheet('QLineEdit { background-color: #%s; padding-right: %ipx; }' % (backColor, selectorWidth + borderWidth))
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
            self.openItem()

    def keyPressEvent(self, keyEvent):
        if keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            key = keyEvent.key()
            if key == QtCore.Qt.Key_Insert:
                self.selectItem()
                return
            elif key == QtCore.Qt.Key_Delete:
                self.clear()
                return
            elif key == QtCore.Qt.Key_Space:
                self.openItem()
                return
        super().keyPressEvent(keyEvent)

    def openItem(self):
        """Open a form for editing the item kept in this widget."""
        if self._db and self._id is not None:
            from wic import forms, getObjectByPath
            model = getObjectByPath(self._model)
            catalogItem = model.getOneById(self._db, self._id)
            forms.openCatalogItemForm(catalogItem)

    def selectItem(self):
        """Open a list of items to replace the current one."""
        if self._db:
            from wic import forms, getObjectByPath
            model = getObjectByPath(self._model)
            catalogForm = forms.openCatalogForm(model, self._db, type = 1)
            catalogForm.itemSelected.connect(self.setId)

    def contextMenuEvent(self, qContextMenuEvent):
        menu = getattr(self, 'menu', None)
        if not menu:
            from wic import menus
            menu = QtGui.QMenu(self) # context menu
            menus.addActionsToMenu(menu, (
                menus.createAction(menu, 'Select', self.selectItem, 'Insert', ':/icons/fugue/cards-stack.png'),
                menus.createAction(menu, 'Open', self.openItem, 'Space', ':/icons/fugue/card-address.png'),
                menus.createAction(menu, 'Clear', self.clear, 'Delete', ':/icons/fugue/eraser.png'),
            ))
            self.menu = menu
        menu.popup(qContextMenuEvent.globalPos())
