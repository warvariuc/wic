from PyQt4 import QtGui
import cfg_tree
import cfg_catalogs
from w_date import Date
from decimal import Decimal as Dec


class CfgFieldNode(cfg_tree.CfgTreeNode):
    dataName = 'field.yaml'
    formName = 'cfg_db_field.ui'
    icon = QtGui.QIcon(':/icons/attribute.png')
    
    def edit(self, parentWidget):
        def beforeShow(dialog):
            dialog.type.addItem('Decimal', 1)
            dialog.type.addItem('String', 2)
            dialog.type.addItem('Date', 3)
            dialog.type.addItem('Float',4)
            dialog.type.addItem('Boolean', 5)
            dialog.type.addItem('Blob', 6)
            
            dialog.type.insertSeparator(dialog.type.count())
            def walkChildren(cfgNode):
                for child in cfgNode.children:
                    if isinstance(child, cfg_catalogs.CfgCatalogNode):
                        dialog.type.addItem('Справочник.' + child.identifier, child.data['id'])
                    walkChildren(child)
            walkChildren(self.root)
            #types = {1: 'Decimal', 2: 'Строка', 3: 'Дата', 4: 'Целое число', 5: 'Булево'}
#            for key, value in types.items():
#                dialog.type.addItem(value, key)
            dialog.type.setCurrentIndex(dialog.type.findData(self.data['type']))
            
        def beforeSave(dialog):
            self.data['type'] = dialog.type.itemData(dialog.type.currentIndex())
        super().edit(parentWidget, beforeShow, beforeSave)

    
CfgFieldNode.createAction('Новое поле', ':/icons/fugue/plus.png', CfgFieldNode.new)
CfgFieldNode.createAction('Удалить поле', ':/icons/fugue/cross.png', CfgFieldNode.delete)
CfgFieldNode.createAction('Свойства поля', ':/icons/fugue/property.png', CfgFieldNode.edit, True)


class CfgFieldsNode(cfg_tree.CfgTreeNode):
    icon = QtGui.QIcon(':/icons/attributes.png')
    childNodeClass = CfgFieldNode
    name = 'Поля'

CfgFieldsNode.createAction('Новое поле', ':/icons/fugue/plus.png', CfgFieldsNode.newChild)
