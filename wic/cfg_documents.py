from PyQt4 import QtCore, QtGui
import os
import md_tree

class MdDocumentsNode(md_tree.MdTreeNode):
    name = 'Документы'
    icon = QtGui.QIcon(':/icons/fugue/documents-stack.png')
    
    def load(self, dirPath) :
        if not os.path.isdir(dirPath) :
            return # specified directory doesn't exist
    
    def handleNew(self, treeView) :
        QtGui.QMessageBox.warning(treeView, '', 'new document')


MdDocumentsNode.createAction('Новый документ', ':/icons/fugue/plus.png', MdDocumentsNode.handleNew)
