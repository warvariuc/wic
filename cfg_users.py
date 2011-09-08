from PyQt4 import QtGui
import hashlib
import cfg_tree


class CfgUserNode(cfg_tree.CfgTreeNode):
    dataName = 'user.yaml'
    formName = 'cfg_user.ui'
    icon = QtGui.QIcon(':/icons/fugue/user.png')
    
    def checkAccept(self, dialog):
        if dialog.password.isModified():
            self.data['password_hash'] = hashlib.sha512(self.data['password'].encode()).hexdigest()
            dialog.password.clear()
            dialog.password.setModified(False)
        super().checkAccept(dialog)

CfgUserNode.createAction('Новый пользователь', ':/icons/fugue/plus.png', CfgUserNode.new)
CfgUserNode.createAction('Удалить пользователя', ':/icons/fugue/cross.png', CfgUserNode.delete)
CfgUserNode.createAction('Свойства пользователя', ':/icons/fugue/property.png', CfgUserNode.edit, True)



class CfgUsersNode(cfg_tree.CfgTreeNode):
    icon = QtGui.QIcon(':/icons/fugue/users.png')
    childNodeClass = CfgUserNode
    name = 'Пользователи'
    

CfgUsersNode.createAction('Новый пользователь', ':/icons/fugue/plus.png', CfgUsersNode.newChild)
