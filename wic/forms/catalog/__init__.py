
__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import sys
from PyQt4 import QtGui, QtCore

import orm
from wic.datetime import DateTime

#from wic import forms, widgets, menus, Bunch # doesn't work (NameError) - http://bugs.python.org/issue992389
# workaround because of circular imports
import wic.forms, wic.widgets, wic.menus
forms = sys.modules['wic.forms']
widgets = sys.modules['wic.widgets']
menus = sys.modules['wic.menus']
from wic import Bunch

from .w_catalog_model import WCatalogViewModel, CatalogModel


class CatalogItemForm(forms.WForm):
    """Form of a catalog item.
    """

    _uiFilePath = None # autogenerated by default
    _formTitle = 'Catalog item'
    _iconPath = ':/icons/fugue/card-address.png'
    _catalogItem = None

    def __init__(self, catalogItem, **kwargs):
        assert isinstance(catalogItem, CatalogModel), 'Must be a catalog item (CatalogModel instance)'
        super().__init__(_catalogItem = catalogItem, **kwargs)

    def setupUi(self):
        """Initial setting up of the form. Reimplemented.
        Dynamically create form fields, if no ui file is supplied. 
        Fill form fields with data from DB.
        """
        self._formTitle = '%s item' % self._catalogItem.__class__
        if not self._uiFilePath: # automatically generated form
            self.createWidgets()
        self.setupWidgets()
        super().setupUi()
        self.fillFormFromItem()

    def createWidgets(self):
        """Automatically create on the form widgets and labels for each catalog model field.
        """
        formLayout = QtGui.QFormLayout(self)
        formLayout.setMargin(2)
        for field in self._catalogItem.__class__:
            fieldName = field.name
            assert not hasattr(self, fieldName), 'Form already has attribute with name `%s`' % fieldName
            widget, label = self.createWidgetForField(field)
            widget.setObjectName(fieldName)
            setattr(self, fieldName, widget)
            #label.setObjectName('label_' + fieldName)
            setattr(self, 'label_' + fieldName, label)
            label.setBuddy(widget)
            formLayout.addRow(label, widget)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset
                        | QtGui.QDialogButtonBox.Save | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName('buttonBox')
        formLayout.addRow(self.buttonBox)
        self.formLayout = formLayout

    def setupWidgets(self):
        """Set up widgets which are mapped to catalog model fields. 
        Connect button box signals to the corresponding handlers.
        """
        for field in self._catalogItem.__class__:
            widget = getattr(self, field.name, None)
            if widget:
                self.setupWidgetForField(widget, field)

    def onReset(self):
        self.fillFormFromItem()

    def fillFormFromItem(self):
        """Automatically fill the form fields using the values from the catalog item fields.
        """
        catalogItem = self._catalogItem
        for field in catalogItem.__class__:
            fieldName = field.name
            fieldValue = catalogItem[field]
            widget = getattr(self, fieldName, None)
            if widget:
                forms.setValue(widget, fieldValue)

    def fillItemFromForm(self):
        """Automatically fill the item field values from the corresponding form widgets.
        """
        catalogItem = self._catalogItem
        for field in catalogItem.__class__:
            fieldName = field.name
            widget = getattr(self, fieldName, None)
            if widget:
                fieldValue = forms.getValue(widget)
                if isinstance(field, orm.IdField) and not fieldValue: # if nothing is entered into Id field - treat it as NULL
                    fieldValue = None
                elif isinstance(field, orm.DateTimeField):
                    if any(char.isdigit() for char in fieldValue):
                        fieldValue = DateTime.strptime(fieldValue, '%Y-%m-%d %H:%M:%S.%f')
                    else:
                        fieldValue = None
                setattr(catalogItem, fieldName, fieldValue)

    def onSave(self):
        """Called when save button is pressed.
        """
        catalogItem = self._catalogItem
        self.fillItemFromForm()
        catalogItem.save()

        # update item id and timestamp on the form
        idWidget = getattr(self, 'id', None)
        if idWidget:
            forms.setValue(idWidget, catalogItem.id)
        timestampWidget = getattr(self, 'timestamp', None)
        if timestampWidget:
            forms.setValue(timestampWidget, catalogItem.timestamp)
        print('save!')


    def createWidgetForField(self, field):
        """Create widget and label for the given model field
        @param field: model field
        @return: tuple (widget, label); widget - QWidget, label - QLabel
        """
        assert isinstance(field, orm.Field)
        label = field.label
        if isinstance(field, (orm.CharField, orm.IntegerField, orm.IdField, orm.DateTimeField)):
            widget = QtGui.QLineEdit()
        elif isinstance(field, orm.DecimalField):
            widget = widgets.WDecimalEdit()
        elif isinstance(field, orm.DateField):
            widget = widgets.WDateEdit()
        elif isinstance(field, orm.BooleanField):
            widget = QtGui.QCheckBox(field.label)
            label = ''
        elif isinstance(field, orm.TextField):
            widget = QtGui.QPlainTextEdit()
        elif isinstance(field, orm.RecordField):
            widget = widgets.WCatalogItemWidget()
        else:
            raise Exception('Could not create a widget for field `%s`' % field)
        return widget, QtGui.QLabel(label)


    def setupWidgetForField(self, widget, field):
        """Set up a widget which corresponds to an model field - only the details related to data entering to appearance.
        The widget might be autocreated or one from a *.ui file.
        """
        assert isinstance(field, orm.Field) and isinstance(widget, QtGui.QWidget)
        if isinstance(field, orm.CharField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setMaxLength(field.column.precision)
        elif isinstance(field, orm.IdField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setValidator(QtGui.QIntValidator())
        elif isinstance(field, orm.DateTimeField):
            if isinstance(widget, QtGui.QLineEdit):
                widget.setInputMask('9999-99-99 99:99:99.999999')
        elif isinstance(field, orm.DecimalField):
            if isinstance(widget, widgets.WDecimalEdit):
                widget.setMaxDigits(field.column.precision)
                widget.setFractionDigits(field.column.scale)
        elif isinstance(field, orm.RecordField):
            if isinstance(widget, widgets.WCatalogItemWidget):
                catalogModel = field.referTable
                widget.setModel(catalogModel.__module__ + '.' + catalogModel.__name__)
                widget.setDb(self._catalogItem._db)




class CatalogForm(forms.WForm):
    """Form with a list of catalog items.
    """

    _uiFilePath = None
    _formTitle = 'Catalog'
    _iconPath = ':/icons/fugue/cards-stack.png'
    _toolbarVisible = True

    _catalogModel = None
    _columns = None # which columns to show in form 'field_name1+100,100 field2,+field3 250,field4 -,field5'
    _viewModel = WCatalogViewModel # you can override this to customize visual appearance

    itemSelected = QtCore.pyqtSignal(CatalogModel)
    _type = 0 # 0: selection causes opening item form, 1: send itemSelected signal and close the form, 2: send signal but do not close the form (for multiple selection) 

    def __init__(self, catalogModel, db, type = 0, **kwargs):
        super().__init__(_catalogModel = catalogModel, _db = db, _type = type, **kwargs)

    def setupUi(self):
        """Initial setting up of the form.
        Dynamically create form widgets, if no ui file is supplied. 
        Fill form fields with data from DB.
        """
        self._formTitle = '%s catalog' % self._catalogModel
        if not self._uiFilePath: # automatically generated form
            self.createWidgets()
        super().setupUi()
        self.toolbar.setVisible(self._toolbarVisible)
        self.tableView.setFocus()
        #self.tableView.resizeColumnsToContents() - too slow - requests all the data from model

    def createWidgets(self):
        """Automatically create on the form widgets.
        """
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
        menu.createItem = menus.createAction(toolbar, 'Create new item', self.createItem, 'Insert', ':/icons/fugue/plus.png')
        menu.editItem = menus.createAction(toolbar, 'Edit selected item', self.editItem, 'Enter', ':/icons/fugue/pencil.png')
        menu.deleteItem = menus.createAction(toolbar, 'Delete selected item', self.deleteItem, 'Delete', ':/icons/fugue/cross.png')
        menus.addActionsToMenu(toolbar, (menu.createItem, menu.editItem, menu.deleteItem))
        toolbar.setIconSize(QtCore.QSize(16, 16))
        self.menu = menu

    def setupTableView(self, tableView):
        assert isinstance(tableView, QtGui.QTableView)
        tableView.setSelectionBehavior(tableView.SelectItems)
        tableView.setSelectionMode(tableView.SingleSelection)
        #self.tableView.verticalHeader().hide()
        tableView.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        rowHeight = QtGui.QFontMetrics(QtGui.QApplication.font()).height() + 4 # font height and some spare pixels
        tableView.verticalHeader().setDefaultSectionSize(rowHeight)
        #tableView.setIconSize(QtCore.QSize(16, 16))
        #tableView.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents) # very slow - it queries all items
        tableView.horizontalHeader().setStretchLastSection(True) # the last visible section in the header takes up all the available space
        tableView.setGridStyle(QtCore.Qt.DotLine)

        tableView.installEventFilter(self)
        tableView.doubleClicked.connect(self.menu.editItem.trigger)
        tableView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        tableView.customContextMenuRequested.connect(self.onTableViewContextMenuRequested)

        catalogViewModel = self._viewModel(self._db, self._catalogModel)
        tableView.setModel(catalogViewModel)
        tableView.selectionModel().selectionChanged.connect(self.onSelectionChanged)

        tableView.selectionModel().setCurrentIndex(tableView.model().index(0, 0), QtGui.QItemSelectionModel.ClearAndSelect)

        catalogViewModel.modelAboutToBeReset.connect(self.onModelAboutToBeReset)
        catalogViewModel.modelReset.connect(self.onModelReset)

        tableView.verticalScrollBar().valueChanged.connect(self.ensureSelectionVisible)
        tableView.horizontalScrollBar().valueChanged.connect(self.ensureSelectionVisible)

    def eventFilter(self, tableView, event): # target - tableView
        #print('eventFilter', event)
        if event.type() == QtCore.QEvent.KeyPress:
            if event.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
                key = event.key()
                if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    self.menu.editItem.trigger()
                    return True
                elif key == QtCore.Qt.Key_End:
                    currentIndex = tableView.selectionModel().currentIndex()
                    tableView.setCurrentIndex(tableView.model().index(tableView.model().rowCount(None) - 1, currentIndex.column()))
                    return True
                elif key == QtCore.Qt.Key_Home:
                    currentIndex = tableView.selectionModel().currentIndex()
                    tableView.setCurrentIndex(tableView.model().index(0, currentIndex.column()))
                    return True
        elif event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() == QtCore.Qt.LeftButton:
                self.menu.editItem.trigger()
                return True
        elif event.type() == QtCore.QEvent.Wheel: # received when scrolling on viewport is on the boundaries
            currentIndex = tableView.selectionModel().currentIndex()
            rowNo = currentIndex.row() - int(event.delta() / 120)
            rowNo = min(max(rowNo, 0), tableView.model().rowCount(None) - 1) # to be sure it's not out of boundaries
            tableView.setCurrentIndex(tableView.model().index(rowNo, currentIndex.column())) # when scrolling on the boundary - move the selection closer to that boundary
            return True

        return super().eventFilter(tableView, event) # standard event processing        

    def ensureSelectionVisible(self, *args):
        """Ensure that selection moves when scrolling - it must be always visible.
        """
        tableView = self.tableView
        currentIndex = tableView.selectionModel().currentIndex()
        viewRect = tableView.viewport().rect()

        row = _row = currentIndex.row()
        column = _column = currentIndex.column()
        topRow = tableView.indexAt(viewRect.topLeft()).row()
        if row < topRow:
            row = topRow
        else:
            row = min(row, tableView.indexAt(viewRect.bottomLeft()).row())
        leftColumn = tableView.indexAt(viewRect.topLeft()).column()
        if column < leftColumn:
            column = leftColumn
        else:
            column = min(column, tableView.indexAt(viewRect.topRight()).column())
        index = tableView.model().index(row, column)
        itemRect = tableView.visualRect(index)
        if itemRect.top() < viewRect.top():
            row += 1
        elif itemRect.bottom() > viewRect.bottom():
            row -= 1
        if itemRect.left() < viewRect.left():
            column += 1
        elif itemRect.right() > viewRect.right():
            column -= 1
        if column != _column or row != _row:
            tableView.setCurrentIndex(tableView.model().index(row, column))

    def onModelAboutToBeReset(self):
        """Remember the selected row when the model is about to be reset.
        """
        currentIndex = self.tableView.selectionModel().currentIndex()
        self._lastSelectedItem = (currentIndex.row(), currentIndex.column())

    def onModelReset(self):
        """Restore the selected item after the model was reset.
        """
        rowNo, colNo = self._lastSelectedItem
        rowNo = min(rowNo, self.tableView.model().rowCount(None) - 1)
        colNo = min(colNo, self.tableView.model().columnCount(None) - 1)
        index = self.tableView.model().index(rowNo, colNo)
        self.tableView.setCurrentIndex(index)

    def onSelectionChanged(self):
        currentIndex = self.tableView.selectionModel().currentIndex()
        self.menu.editItem.setEnabled(currentIndex.isValid())

    def onTableViewContextMenuRequested(self, coord):
        menu = QtGui.QMenu(self.tableView)
        menus.addActionsToMenu(menu, (self.menu.createItem, self.menu.editItem, self.menu.deleteItem))
        menu.popup(self.tableView.viewport().mapToGlobal(coord))


    def createItem(self):
        catalogItem = self._catalogModel(self._db)
        openCatalogItemForm(catalogItem)

    def editItem(self):
        currentIndex = self.tableView.selectionModel().currentIndex()
        catalogItem = self.tableView.model().item(currentIndex.row())
        if self._type == 0:
            openCatalogItemForm(catalogItem)
        elif self._type == 1: # emit signal and close the form
            self.itemSelected.emit(catalogItem)
            self.close()
        else: # emit signal but do not close the form
            self.itemSelected.emit(catalogItem)

    def deleteItem(self):
        if QtGui.QMessageBox.question(self, 'Delete', 'Are you sure?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Yes:
            currentIndex = self.tableView.selectionModel().currentIndex()
            catalogItem = self.tableView.model().item(currentIndex.row())
            catalogItem.delete()



def openCatalogItemForm(catalogItem, FormClass = None, **kwargs):
    assert isinstance(catalogItem, orm.Model), 'Pass a catalog item (CatalogModel instance).'
    if FormClass is None:
        formModulePath = catalogItem.__class__.__module__
        FormClass = getattr(sys.modules[formModulePath], 'Form', None)
        if FormClass is None: # if user form not present - take CatalogItemForm with autogenerated widgets
            FormClass = CatalogItemForm
            _uiFilePath = ''
        else:
            _uiFilePath = FormClass._uiFilePath
        kwargs['_uiFilePath'] = _uiFilePath
    kwargs['catalogItem'] = catalogItem

    if not isinstance(FormClass, type) and issubclass(FormClass, CatalogItemForm):
        raise forms.FormNotFoundError('This is not a CatalogItemForm')

    return forms.openForm(FormClass, **kwargs)


def openCatalogForm(catalogModel, db, FormClass = None, **kwargs):
    if isinstance(catalogModel, str):
        catalogModel = wic.getObjectByPath(catalogModel)
    assert isinstance(catalogModel, orm.ModelMeta), 'Pass a model class.'
    catalogModel.checkTable(db) # before opening the form
    if not FormClass:
        formModulePath = catalogModel.__module__
        FormClass = getattr(sys.modules[formModulePath], 'CatalogForm', CatalogForm)

    assert issubclass(FormClass, CatalogForm), 'This is not a CatalogForm'
    kwargs['catalogModel'] = catalogModel
    kwargs['db'] = db
    return forms.openForm(FormClass, **kwargs)
