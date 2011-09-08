from PyQt4 import QtGui, QtCore
import os
import re
import shutil
import w


class CfgTreeNode():
    "This class defines a node of metadata tree. Tree nodes inherit this class."
    identifier = '' #text identifier: starts with '_' or a letter and contains letters, digits and underscore
    icon = QtGui.QIcon(':/icons/fugue/block.png')

    def __init__(self, cfgRoot, parentNode=None, row=None):
        self.root = cfgRoot #CfgTreeNode
        self.parent = None
        self.children = []
        self.data = {}
        if cfgRoot: self.data['id'] = cfgRoot.getNextId()
        self.setParent(parentNode, row)
        
    def modelIndex(self):
        'return model index of this configuration node'
        parentIndex = self.parent.modelIndex() if self.parent else QtCore.QModelIndex()
        root = self.root or self # if node doesn't have root - it is the root itself
        return root.model.index(self.row(), 0, parentIndex)
        
    def setParent(self, parent=None, row=None):
        if parent:
            if 'id' in self.data and self.root.getNodeById(self.data['id']):
                w.printMessage('Попытка присоедения узла с повторным id: ' + os.path.join(self.dirPath, self.identifier))
                return
            self.setParent() #if there is already another parent - remove it
            if row is None: row = len(parent.children)
            parentIndex = parent.modelIndex()
            self.root.model.layoutAboutToBeChanged.emit()
            self.root.model.beginInsertRows(parentIndex, row, row)
            parent.children.insert(row, self) #insert at specified row
            self.parent = parent
            self.root.model.endInsertRows()
            self.root.model.layoutChanged.emit()        
        elif self.parent: #remove parent
            row = self.row()
            parentIndex = self.parent.modelIndex()
            self.root.model.layoutAboutToBeChanged.emit()
            self.root.model.beginRemoveRows(parentIndex, row, row)
            self.parent.children.remove(self)
            self.parent = None
            self.root.model.endRemoveRows()
            self.root.model.layoutChanged.emit()

    def row(self): #returns which position the node has among its siblings
        return self.parent.children.index(self) if self.parent else 0

    def load(self, dirPath):
        self.dirPath, self.identifier = os.path.split(dirPath)
        if self.identifier != sanitizeIdentifier(self.identifier):
            print('Неправильный идентификатор узла: ' + self.identifier)
            return False
        self.data.update(w.loadFromFile(os.path.join(dirPath, self.dataName)))
        return True #the data was loaded successfully and correctly

    def loadChildren(self, dirPath):
        self.data['name'] = self.name

        self.dirPath, self.identifier = os.path.split(dirPath)
        if not os.path.isdir(dirPath): # specified directory doesn't exist
            os.makedirs(dirPath)

        for subDir in os.listdir(dirPath):
            subDir = os.path.join(dirPath, subDir)
            if os.path.isdir(subDir):
                cfgNode = self.childNodeClass(self.root) #unparented for now
                if cfgNode.load(subDir): # данные загружены успешно
                    cfgNode.setParent(self)
                
    def save(self):
        obj = self
        objPath = obj.identifier
        while True:
            objPath = obj.identifier + '/' + objPath
            obj = obj.parent
            if not obj: break
        w.printMessage('Сохранение узла: ' + objPath)
        w.saveToFile(self.data, os.path.join(self.dirPath, self.identifier, self.dataName))
        
    def delete(self, parentWidget):
        linkedNodes = self.root.getLinkedNodes(self)
        if linkedNodes:
            QtGui.QMessageBox.warning(parentWidget, 'Есть ссылки',
                'Узел нельзя удалить - на него есть ссылки в других узлах.')
            w.printMessage('<b>Узел <a href="">"{}"</a> использован в:</b>'.format(self.root.nodePath(self)))
            for node in linkedNodes:
                w.printMessage(self.root.nodePath(node))
            return
        if QtGui.QMessageBox.question(parentWidget, 'Подтверждение',
                'Вы действительно хотите удалить узел?', QtGui.QMessageBox.Yes, 
                QtGui.QMessageBox.No) != QtGui.QMessageBox.Yes:
            return
        nodeDir = os.path.join(self.dirPath, self.identifier)
        try: shutil.rmtree(nodeDir) # может сначала переместить папку в другое место, а потом удалить, чтобы не было полуудаления?
        except Exception as exc: 
            QtGui.QMessageBox.warning(parentWidget, 'Узел', 
                    'Не удалось удалить директорию узла конфигурации\n'
                    '(возможно, есть файлы только для чтения):\n' + nodeDir + '\n' + str(exc))
            return
        self.root.log('Удалена директория узла конфигурации: ' + nodeDir)
        self.setParent() #unparent the node. after all references gone - python will delete the object and its children
        
        
    @classmethod
    def createAction(cls, text, icon, slot, isDefault = False):
        action = QtGui.QAction(QtGui.QIcon(icon), text, None)
        action.setData(slot) # in data we store the function to call
        if not hasattr(cls, 'actions'): 
            cls.actions = []
            cls.defaultAction = None
        cls.actions.append(action)
        if isDefault:
            font = QtGui.QFont()
            font.setBold(True)
            action.setFont(font)
            cls.defaultAction = action
        return action

    def newChild(self, treeView):
        'Создать узел и открыть форму для его редактирования.'
        dirPath = os.path.join(self.dirPath, self.identifier)
        templateDir = os.path.join(QtGui.qApp.appDir, 'templates', self.identifier)
        if not os.path.isdir(templateDir):
            QtGui.QMessageBox.warning(treeView, 'Шаблон узла', 
                    'Не найден шаблон узла конфигурации:\n' + templateDir)
            return
        data = w.loadFromFile(os.path.join(templateDir, self.childNodeClass.dataName))
        identifier = data['identifier'] # default identifier from template
        i = 0
        while True:
            i += 1
            _identifier = identifier + str(i)
            newNodeDir = os.path.join(dirPath, _identifier)
            if not os.path.exists(newNodeDir): break
        
        try: shutil.copytree(templateDir, newNodeDir)
        except Exception as exc: 
            QtGui.QMessageBox.warning(treeView, 'Узел', 
                    'Не удалось создать директорию нового узла конфигурации:\n' 
                    + newNodeDir + '\n' + str(exc))
            return
        self.root.log('Создана директория нового узла конфигурации: ' + newNodeDir)

        cfgNode = self.childNodeClass(self.root, self)
        cfgNode.load(os.path.join(dirPath, _identifier))
        treeView.expand(self.modelIndex())
        treeView.selectionModel().select(cfgNode.modelIndex(), QtGui.QItemSelectionModel.ClearAndSelect)
        treeView.expand(cfgNode.modelIndex())        
        cfgNode.edit(treeView)
            
    def new(self, treeView):
        'Создание нового узла. По умолчанию - вызвать реализацию родителя.'
        self.parent.newChild(treeView)

    def edit(self, parentWidget, beforeShowFunc=None, beforeSaveFunc=None):
        self.data['identifier'] = self.identifier
        dialog = w.putToForm(self.data, os.path.join(QtGui.qApp.appDir, 'forms', self.formName), parentWidget)
        dialog.buttonBox.accepted.connect(lambda dialog=dialog: self.checkAccept(dialog, beforeSaveFunc))
        if beforeShowFunc: beforeShowFunc(dialog)
        dialog.exec()

    def checkAccept(self, dialog, beforeSaveFunc=None):
        try: identifier = dialog.identifier.text()
        except AttributeError: pass #the form might not have identifier widget
        else:
            if not identifier:
                QtGui.QMessageBox.warning(dialog, 'Идентификатор',
                        'Текстовый идентификатор не может быть пустым.')
                return
            good_id = sanitizeIdentifier(identifier)
            if good_id != dialog.identifier.text():
                dialog.identifier.setText(good_id)
                QtGui.QMessageBox.warning(dialog, 'Идентификатор',
                        'Текстовый идентификатор, который вы ввели,\n'
                        'был исправлен, чтобы соответствовать требованиям.')
                return # identifier was sanitized, don't close the dialog - the user must see changes
            newNodeDir = os.path.join(self.dirPath, identifier)
            if identifier != self.identifier: # existing node has a new identifier
                oldNodeDir = os.path.join(self.dirPath, self.identifier)
                try: os.rename(oldNodeDir, newNodeDir) #rename node directory
                except Exception as exc: 
                    QtGui.QMessageBox.warning(dialog, 'Узел', 
                            'Не удалось переименовать директорию узла конфигурации:\n'
                            + newNodeDir + '\n' + str(exc))
                    return
                    
            self.data.update(w.getFromForm(dialog))
            self.identifier = self.data['identifier']
            del self.data['identifier']
            if beforeSaveFunc: beforeSaveFunc(dialog)
            self.save()

            dialog.accept()

#####################################################################################

class CfgTreeModel(QtCore.QAbstractItemModel):
    def __init__(self):
        super().__init__()
        self.load(QtGui.qApp.confDir)

    def load(self, dirPath):
        import cfg_root, cfg_reports
        import cfg_users, cfg_catalogs#, md_documents
        self.cfgRoot = cfg_root.CfgRootNode(self) # root node
        self.cfgRoot.load(dirPath)
        cfg_catalogs.CfgCatalogsNode(self.cfgRoot, self.cfgRoot).loadChildren(os.path.join(dirPath, 'catalogs'))
        cfg_reports.CfgReportsNode(self.cfgRoot, self.cfgRoot).loadChildren(os.path.join(dirPath, 'reports'))
#        md_documents.MdDocumentsNode(self.cfgRoot, self.cfgRoot).loadChildren(os.path.join(dirPath, 'documents'))
        cfg_users.CfgUsersNode(self.cfgRoot, self.cfgRoot).loadChildren(os.path.join(dirPath, 'users'))

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if 0 <= row < self.rowCount(parent) and 0 <= column < self.columnCount(parent):
            childItem = parent.internalPointer().children[row] if parent.isValid() else self.cfgRoot
            return self.createIndex(row, column, childItem)
        return QtCore.QModelIndex() 

    def parent(self, index):
        if index.isValid():
            mdParentNode = index.internalPointer().parent
            if mdParentNode:
                return self.createIndex(mdParentNode.row(), 0, mdParentNode)
        return QtCore.QModelIndex()
        
    def columnCount(self, parent): return 1

    def rowCount(self, parent):
        return len(parent.internalPointer().children) if parent.isValid() else 1 #there just one top level item - the root - CfgRoot

    def data(self, index, role):
        if index.isValid():
            cfgNode = index.internalPointer()
            if role == QtCore.Qt.DisplayRole:
                return cfgNode.data['name'] or cfgNode.identifier
            if role == QtCore.Qt.DecorationRole:
                return cfgNode.icon
        return None
        


def sanitizeIdentifier(identifier):
    return re.sub('\W|^(?=\d)', '_', identifier) #http://stackoverflow.com/questions/3303312/how-do-i-convert-a-string-to-a-valid-variable-name-in-python
    
