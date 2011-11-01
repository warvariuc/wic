from PyQt4 import QtCore, QtGui
import os

class MdSaveWindow(QtGui.QDialog): # window to interactively handle metadata saving
    def __init__(self, parentWidget, mdRootNode):
        super().__init__(parentWidget, QtCore.Qt.WindowMaximizeButtonHint)
        self.setWindowTitle('Сохранение конфигурации')
        
        self.treeWidget = MdTreeWidget(self, mdRootNode)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.treeWidget)
        
        #self.resize()
        
        self.treeWidget.compare()

    #def closeEvent(self, event):
    #    event.accept()
    #    self.parentWidget().close() # close sub window



class MdTreeWidget(QtGui.QTreeWidget):
    def __init__(self, parent, mdRootNode):
        super().__init__(parent)
        self.setRootIsDecorated(False)
        self.mdRootNode = mdRootNode
#        self.setItemDelegate(VariantDelegate(self))

        self.setHeaderLabels(("Узел", "Действие", "Значение"))
        #self.header().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.header().setResizeMode(2, QtGui.QHeaderView.Stretch)

#        self.groupIcon = QtGui.QIcon()
#        self.groupIcon.addPixmap(self.style().standardPixmap(QtGui.QStyle.SP_DirClosedIcon),
#                QtGui.QIcon.Normal, QtGui.QIcon.Off)
#        self.groupIcon.addPixmap(self.style().standardPixmap(QtGui.QStyle.SP_DirOpenIcon),
#                QtGui.QIcon.Normal, QtGui.QIcon.On)
#        self.keyIcon = QtGui.QIcon()
#        self.keyIcon.addPixmap(self.style().standardPixmap(QtGui.QStyle.SP_FileIcon))

    def sizeHint(self):
        return QtCore.QSize(800, 600)

    def compare(self):
        after = None

#        if index != 0:
#            after = self.childAt(parent, index - 1)
#
#        if parent is not None:
#            item = QtGui.QTreeWidgetItem(parent, after)
#        else:
        item = QtGui.QTreeWidgetItem(self, after)

        item.setText(0, self.mdRootNode.name)
        #item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(0, QtCore.Qt.Checked) #By default, items are enabled, selectable, checkable, and can be the source of a drag and drop operation.
        
        self.resizeColumnToContents(0)
