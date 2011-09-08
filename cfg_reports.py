from PyQt4 import QtGui
import os
import w
import cfg_tree


class CfgReportNode(cfg_tree.CfgTreeNode):
    dataName = 'report.yaml'
    formName = 'cfg_report.ui'
    icon = QtGui.QIcon(':/icons/fugue/report.png')
    
    def editForm(self, treeView):
        w.editForm(os.path.join(self.dirPath, self.identifier, 'form.ui'))
    
    def editModule(self, treeView):
        w.editModule(os.path.join(self.dirPath, self.identifier, 'module.py'))

CfgReportNode.createAction('Новый отчёт', ':/icons/fugue/plus.png', CfgReportNode.new)
CfgReportNode.createAction('Удалить отчёт', ':/icons/fugue/cross.png', CfgReportNode.delete)
CfgReportNode.createAction('Редактировать форму', ':/icons/fugue/application-form.png', CfgReportNode.editForm)
CfgReportNode.createAction('Редактировать модуль', ':/icons/fugue/script-code.png', CfgReportNode.editModule)
CfgReportNode.createAction('Свойства отчёта', ':/icons/fugue/property.png', CfgReportNode.edit, True)


class CfgReportsNode(cfg_tree.CfgTreeNode):
    icon = QtGui.QIcon(':/icons/fugue/reports-stack.png')
    childNodeClass = CfgReportNode
    name = 'Отчёты'

CfgReportsNode.createAction('Новый отчёт', ':/icons/fugue/plus.png', CfgReportsNode.newChild)
