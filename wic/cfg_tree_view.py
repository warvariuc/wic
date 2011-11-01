from PyQt4 import QtCore, QtGui
import cfg_tree

class CfgTreeView(QtGui.QTreeView):
    def __init__(self, parentWidget):
        super().__init__(parentWidget)
        self.treeModel = cfg_tree.CfgTreeModel()
        self.setModel(self.treeModel)
        self.setSelectionBehavior(QtGui.QTreeView.SelectItems)
        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)
        self.setExpandsOnDoubleClick(False)
        self.setRootIsDecorated(False)
        #self.expandAll()
        self.expand(self.model().index(0, 0, QtCore.QModelIndex())) #expand root
        self.show()

        #self.treeModel.dataChanged.connect(lambda: self.setWindowModified(True))
        
    def contextMenuEvent(self, contextMenuEvent):
        contextMenuEvent.accept()
        if contextMenuEvent.reason() == QtGui.QContextMenuEvent.Mouse:
            modelIndex = self.indexAt(contextMenuEvent.pos())
            coord = contextMenuEvent.globalPos()
        else:
            modelIndex = self.currentIndex()
            coord = self.viewport().mapToGlobal(self.visualRect(modelIndex).bottomLeft())
        if not modelIndex.isValid(): return
        
        menu = QtGui.QMenu(self)
        for action in modelIndex.internalPointer().actions:
            menu.addAction(action)
        action = menu.exec(coord)
        if action:
            action.data()(modelIndex.internalPointer(), self) #а если там не функция?
     
    def mouseDoubleClickEvent(self, mouseEvent):
        mdNode = self.indexAt(mouseEvent.pos()).internalPointer()
        defaultAction = mdNode.defaultAction
        if defaultAction: 
            defaultAction.data()(mdNode, self)
            return
        super().mouseDoubleClickEvent(mouseEvent)

    def keyPressEvent (self, keyEvent):
        if keyEvent.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter) and\
                keyEvent.modifiers() in (QtCore.Qt.NoModifier, QtCore.Qt.KeypadModifier):
            mdNode = self.currentIndex().internalPointer()
            try:
                mdNode.defaultAction.data()(mdNode, self)
                keyEvent.accept()
            except: pass
        else:
            super().keyPressEvent(keyEvent)

