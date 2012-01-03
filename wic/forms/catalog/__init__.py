"""Author: Victor Varvariuc <victor.varvariuc@gmail.com"""

import sys
from PyQt4 import QtGui, QtCore

import orm

from wic.widgets import w_date_edit, w_decimal_edit, w_record_id_widget
from wic.menu import createAction, addActionsToMenu
from wic.forms import WForm, getValue, setValue, openForm, FormNotFoundError
from .w_catalog_model import WCatalogProxyModel, CatalogModel
from wic import Bunch


class CatalogItemForm(WForm):
    """Form of a catalog item."""

    _uiFilePath = None # autogenerated by default
    _formTitle = 'Catalog item'
    _iconPath = ':/icons/fugue/card-address.png'
    _catalogItem = None

    def __init__(self, _catalogItem, **kwargs):
        assert isinstance(_catalogItem, CatalogModel), 'Must be a catalog item (CatalogModel instance)'
        super().__init__(_catalogItem=_catalogItem, **kwargs)

    def setupUi(self):
        """Initial setting up of the form. Reimplemented.
        Dynamically create form fields, if no ui file is supplied. 
        Fill form fields with data from DB."""
        self._formTitle = '%s item' % self._catalogItem.__class__
        if not self._uiFilePath: # automatically generated form
            self.createWidgets()
        self.setupWidgets()
        super().setupUi()
        self.fillFormFromItem()

    def createWidgets(self):
        """Automatically create on the form widgets and labels for each catalog model field."""
        formLayout = QtGui.QFormLayout(self)
        formLayout.setMargin(2)
        for field in self._catalogItem.__class__:
            fieldName = field.name
            assert not hasattr(self, fieldName), 'Form already has attribute with name `%s`' % fieldName
            labelName = 'label_' + fieldName
            label = QtGui.QLabel(field.label)
            label.setObjectName(labelName)
            widget = self.createWidgetForField(field)
            widget.setObjectName(fieldName)
            setattr(self, fieldName, widget)
            label.setBuddy(widget)
            formLayout.addRow(label, widget)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset
                        | QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName('buttonBox')
        formLayout.addRow(self.buttonBox)
        self.formLayout = formLayout

    def setupWidgets(self):
        """Set up widgets which are mapped to catalog model fields. 
        Connect button box signals to the corresponding handlers."""
        for field in self._catalogItem.__class__:
            widget = getattr(self, field.name, None)
            if widget:
                self.setupWidgetForField(widget, field)

    def onReset(self):
        self.fillFormFromItem()
    
    def fillFormFromItem(self):
        'Automatically fill the form fields using values from the catalog item fields.'
        catalogItem = self._catalogItem
        for field in catalogItem.__class__:
            fieldName = field.name
            fieldValue = catalogItem[field]
            widget = getattr(self, fieldName, None)
            if widget:
                setValue(widget, fieldValue)

    def fillItemFromForm(self):
        'Automatically fill the item field values from the corresponding form widgets.'
        catalogItem = self._catalogItem
        for field in catalogItem.__class__:
            fieldName = field.name
            widget = getattr(self, fieldName, None)
            if widget:
                fieldValue = getValue(widget)
                if isinstance(field, (orm.IdField, orm.RecordIdField)) and not fieldValue:
                    fieldValue = None
                setattr(catalogItem, fieldName, fieldValue)

    def onSave(self):
        """Called when save button is pressed."""
        catalogItem = self._catalogItem
        self.fillItemFromForm()
        catalogItem.save()

        # update item id and timestamp on the form
        idWidget = getattr(self, 'id', None)
        if idWidget:
            setValue(idWidget, catalogItem.id)
        timestampWidget = getattr(self, 'timestamp', None)
        if timestampWidget:
            setValue(timestampWidget, catalogItem.timestamp)
        print('save!')


    def createWidgetForField(self, field):
        assert isinstance(field, orm.Field)
        if isinstance(field, (orm.CharField, orm.IntegerField, orm.IdField, orm.DateTimeField)):
            return QtGui.QLineEdit()
        elif isinstance(field, orm.DecimalField):
            return w_decimal_edit.WDecimalEdit()
        elif isinstance(field, orm.DateField):
            return w_date_edit.WDateEdit()
        elif isinstance(field, orm.BooleanField):
            return QtGui.QCheckBox(field.label)
        elif isinstance(field, orm.TextField):
            return QtGui.QPlainTextEdit()
        elif isinstance(field, orm.RecordIdField):
            return w_record_id_widget.WRecordIdWidget()
        raise Exception('Could not create a widget for field %s' % field)

    def setupWidgetForField(self, widget, field):
        """Set up a widget which corresponds to an model field - only the details related to data entering to appearance.
        The widget might be autocreated or one from a *.ui file."""
        assert isinstance(field, orm.Field) and isinstance(widget, QtGui.QWidget)
        if isinstance(field, orm.CharField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setMaxLength(field.maxLength)
        elif isinstance(field, orm.IdField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setValidator(QtGui.QIntValidator())
        elif isinstance(field, orm.DateTimeField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setInputMask('9999-99-99 99:99:99.999999')
        elif isinstance(field, orm.DecimalField):
            if isinstance(widget, w_decimal_edit.WDecimalEdit):
                widget.setMaxDigits(field.maxDigits)
                widget.setFractionDigits(field.fractionDigits)
        elif isinstance(field, orm.RecordIdField):
            if isinstance(widget, w_record_id_widget.WRecordIdWidget):
                catalogModel = field.table
                widget.setModel(catalogModel.__module__ + '.' + catalogModel.__name__)
                widget.setDb(self._catalogItem._db)




class CatalogForm(WForm):
    """Form with a list of catalog items."""

    _uiFilePath = None
    _formTitle = 'Catalog'
    _iconPath = ':/icons/fugue/cards-stack.png'
    _catalogModel = None
    _toolbarVisible = True

    #editRequested = QtCore.pyqtSignal()

    def __init__(self, _catalogModel, _db):
        super().__init__(_catalogModel=_catalogModel, _db=_db)

    def setupUi(self):
        """Initial setting up of the form.
        Dynamically create form widgets, if no ui file is supplied. 
        Fill form fields with data from DB."""
        self._formTitle = '%s catalog' % self._catalogModel
        if not self._uiFilePath: # automatically generated form
            self.createWidgets()
        super().setupUi()
        self.toolbar.setVisible(self._toolbarVisible)
        self.tableView.setFocus()
        #self.tableView.resizeColumnsToContents() - too slow - requests all the data from model

        self.tableView.selectRow(0)

    def createWidgets(self):
        """Automatically create on the form widgets."""
        layout = QtGui.QVBoxLayout(self)
        layout.setMargin(2)

        self.toolbar = QtGui.QToolBar()
        self.setupToolbar(self.toolbar)
        layout.addWidget(self.toolbar)

        self.tableView = QtGui.QTableView()
        self.setupTableView(self.tableView)
        layout.addWidget(self.tableView)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
        layout.addWidget(self.buttonBox) # add standard button box at the bottom

        self.layout = layout

    def setupToolbar(self, toolbar):
        assert isinstance(toolbar, QtGui.QToolBar)
        menu = Bunch()
        menu.createItem = createAction(toolbar, 'Create new item', self.createItem, 'Insert', ':/icons/fugue/plus.png')
        menu.editItem = createAction(toolbar, 'Edit selected item', self.editItem, 'Enter', ':/icons/fugue/pencil.png')
        menu.deleteItem = createAction(toolbar, 'Delete selected item', self.deleteItem, 'Delete', ':/icons/fugue/cross.png')
        addActionsToMenu(toolbar, (menu.createItem, menu.editItem, menu.deleteItem))
        toolbar.setIconSize(QtCore.QSize(16, 16))
        self.menu = menu

    def setupTableView(self, tableView):
        assert isinstance(tableView, QtGui.QTableView)
        tableView.setSelectionBehavior(tableView.SelectRows)
        tableView.setSelectionMode(tableView.SingleSelection)
        #self.tableView.verticalHeader().hide()
        tableView.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        rowHeight = QtGui.QFontMetrics(QtGui.QApplication.font()).height() + 4
        tableView.verticalHeader().setDefaultSectionSize(rowHeight)
        #tableView.setIconSize(QtCore.QSize(16, 16))
        tableView.horizontalHeader().setStretchLastSection(True) # the last visible section in the header takes up all the available space
        tableView.setGridStyle(QtCore.Qt.DotLine)

        tableView.installEventFilter(self)
        tableView.doubleClicked.connect(self.menu.editItem.trigger)
        tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tableView.customContextMenuRequested.connect(self.onTableViewContextMenuRequested)

        catalogProxyModel = WCatalogProxyModel(self._db, self._catalogModel)
        tableView.setModel(catalogProxyModel)
        tableView.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        catalogProxyModel.modelAboutToBeReset.connect(self.onModelAboutToBeReset)
        catalogProxyModel.modelReset.connect(self.onModelReset)

        tableView.verticalScrollBar().valueChanged.connect(self.onScrollBarValueChanged)

    def eventFilter(self, tableView, event): # target - tableView
        #print('eventFilter', event)
        if event.type() == QtCore.QEvent.KeyPress:
            if event.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
                key = event.key()
                if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    self.menu.editItem.trigger()
                    return True
                elif key == QtCore.Qt.Key_End:
                    event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_End, QtCore.Qt.ControlModifier)
                    QtCore.QCoreApplication.sendEvent(tableView, event)
                    return True
                elif key == QtCore.Qt.Key_Home:
                    event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, QtCore.Qt.Key_Home, QtCore.Qt.ControlModifier)
                    QtCore.QCoreApplication.sendEvent(tableView, event)
                    return True
        elif event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() == QtCore.Qt.LeftButton:
                self.menu.editItem.trigger()
                return True
        elif event.type() == QtCore.QEvent.Wheel: # received when scrolling on viewport is on the boundaries
            currentIndex = tableView.selectionModel().currentIndex()
            tableView.selectRow(currentIndex.row() - int(event.delta() / 120)) # when scrolling on the boundary - move the selection closer to that boundary
            return True

        return super().eventFilter(tableView, event) # standard event processing        

    def onScrollBarValueChanged(self, value):
        "Ensure that selected row moves when scrolling - it must be always visible."
        tableView = self.tableView
        currentRow = tableView.selectionModel().currentIndex().row()
        rect = tableView.viewport().rect()
        topRow = tableView.indexAt(rect.topLeft()).row()
        if currentRow < topRow:
            tableView.selectRow(topRow + 1)
        else:
            bottomRow = tableView.indexAt(rect.bottomLeft()).row()
            if currentRow > bottomRow:
                tableView.selectRow(bottomRow - 1)

    def onModelAboutToBeReset(self):
        "Remember the selected row when the model is reset."
        currentIndex = self.tableView.selectionModel().currentIndex()
        self._lastSelectedRow = currentIndex.row()

    def onModelReset(self):
        "Restore the selected row after the model was reset."
        #self.tableView.resizeColumnsToContents()
        rowNo = min(self._lastSelectedRow, self.tableView.model().rowCount(None) - 1)
        self.tableView.selectRow(rowNo)

    def onSelectionChanged(self):
        currentIndex = self.tableView.selectionModel().currentIndex()
        self.menu.editItem.setEnabled(currentIndex.isValid())

    def onTableViewContextMenuRequested(self, coord):
        menu = QtGui.QMenu(self.tableView)
        addActionsToMenu(menu, (self.menu.createItem, self.menu.editItem, self.menu.deleteItem))
        menu.popup(self.tableView.viewport().mapToGlobal(coord))


    def createItem(self):
        catalogItem = self._catalogModel(self._db)
        openCatalogItemForm(catalogItem)

    def editItem(self):
        currentIndex = self.tableView.selectionModel().currentIndex()
        id = self.tableView.model().getRowId(currentIndex.row())
        catalogItem = self._catalogModel.getOneById(self._db, id)
        openCatalogItemForm(catalogItem)

    def deleteItem(self):
        if QtGui.QMessageBox.question(self, 'Delete', 'Are you sure?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Yes:
            currentIndex = self.tableView.selectionModel().currentIndex()
            id = self.tableView.model().getRowId(currentIndex.row())
            catalogItem = self._catalogModel.getOneById(self._db, id)
            catalogItem.delete()



def openCatalogItemForm(catalogItem, FormClass=None, **kwargs):
    assert isinstance(catalogItem, orm.Model), 'Pass an item (model instance).'
    if FormClass is None:
        formModulePath = catalogItem.__class__.__module__
        FormClass = getattr(sys.modules[formModulePath], 'Form', None)
        if FormClass is None: # if user form not present - take CatalogItemForm with autogenerated widgets
            FormClass = CatalogItemForm
            _uiFilePath = ''
        else:
            _uiFilePath = FormClass._uiFilePath
        kwargs['_uiFilePath'] = _uiFilePath
    kwargs['_catalogItem'] = catalogItem

    if not isinstance(FormClass, type) and issubclass(FormClass, CatalogItemForm):
        raise FormNotFoundError('This is not a CatalogItemForm')

    return openForm(FormClass, **kwargs)


def openCatalogForm(catalogModel, db, FormClass=None, **kwargs):
    assert orm.isModel(catalogModel), 'Pass a model class.'
    if not FormClass:
        formModulePath = catalogModel.__module__
        FormClass = getattr(sys.modules[formModulePath], 'CatalogForm', CatalogForm)

    assert issubclass(FormClass, CatalogForm), 'This is not a CatalogForm'
    kwargs['_catalogModel'] = catalogModel
    kwargs['_db'] = db
    return openForm(FormClass, **kwargs)
