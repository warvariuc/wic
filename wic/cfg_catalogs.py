from PyQt4 import QtGui
import os
import w
import cfg_tree
import cfg_fields


class CfgCatalogNode(cfg_tree.CfgTreeNode):
    dataName = 'catalog.yaml'
    formName = 'cfg_catalog.ui'
    icon = QtGui.QIcon(':/icons/fugue/card-address.png')
    
    def load(self, dirPath):
        if super().load(dirPath):
            cfg_fields.CfgFieldsNode(self.root, self).loadChildren(os.path.join(dirPath, 'fields'))
            return True
        return False
    
    def editForm(self, treeView):
        w.editForm(os.path.join(self.dirPath, self.identifier, 'form.ui'))

    def editListForm(self, treeView):
        pass #w.editForm(os.path.join(self.dirPath, self.identifier, 'form.ui'))

    def editModule(self, treeView):
        w.editModule(os.path.join(self.dirPath, self.identifier, 'module.py'))

CfgCatalogNode.createAction('Новый справочник', ':/icons/fugue/plus.png', CfgCatalogNode.new)
CfgCatalogNode.createAction('Удалить справочник', ':/icons/fugue/cross.png', CfgCatalogNode.delete)
CfgCatalogNode.createAction('Редактировать форму', ':/icons/fugue/application-form.png', CfgCatalogNode.editForm)
CfgCatalogNode.createAction('Редактировать форму списка', ':/icons/fugue/application-form.png', CfgCatalogNode.editListForm)
CfgCatalogNode.createAction('Редактировать модуль', ':/icons/fugue/script-code.png', CfgCatalogNode.editModule)
CfgCatalogNode.createAction('Свойства справочника', ':/icons/fugue/property.png', CfgCatalogNode.edit, True)


class CfgCatalogsNode(cfg_tree.CfgTreeNode):
    icon = QtGui.QIcon(':/icons/fugue/cards-address.png')
    childNodeClass = CfgCatalogNode
    name = 'Справочники'

CfgCatalogsNode.createAction('Новый справочник', ':/icons/fugue/plus.png', CfgCatalogsNode.newChild)

