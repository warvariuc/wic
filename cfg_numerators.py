from PyQt4 import QtGui
import cfg_tree


class CfgNumeratorNode(cfg_tree.CfgTreeNode):
    'Нумератор - нумерует объекты (документы, элементы справочников, ...) согласно заданным правилам.'
    dataName = 'numerator.yaml'
    formName = 'cfg_numerator.ui'
    icon = QtGui.QIcon(':/icons/fugue/counter.png')
    
CfgNumeratorNode.createAction('Новый нумератор', ':/icons/fugue/plus.png', CfgNumeratorNode.new)
CfgNumeratorNode.createAction('Удалить нумератор', ':/icons/fugue/cross.png', CfgNumeratorNode.delete)
CfgNumeratorNode.createAction('Свойства нумератора', ':/icons/fugue/property.png', CfgNumeratorNode.edit, True)



class CfgNumeratorsNode(cfg_tree.CfgTreeNode):
    icon = QtGui.QIcon(':/icons/fugue/users.png')
    childNodeClass = CfgNumeratorNode
    name = 'Пользователи'

CfgNumeratorsNode.createAction('Новый нумератор', ':/icons/fugue/plus.png', CfgNumeratorsNode.newChild)
