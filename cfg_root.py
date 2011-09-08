#from PyQt4 import QtGui
import os
import datetime
import cfg_tree
import w

class CfgRootNode(cfg_tree.CfgTreeNode):
    'Данный класс описывает корень дерева конфигурации - свойства конфигурации.'
    dataName = 'configuration.yaml'
    formName = 'cfg_root.ui'
    
    def __init__(self, model):
        self.model = model
        super().__init__(None) # no root, no parent

    def log(self, textLine):
        'Write a text line to configuration log file'
        logFilename = os.path.join(self.dirPath, self.identifier, 'log.txt')
        with open(logFilename, 'a', encoding='utf8') as file:
            file.write(str(datetime.datetime.today()) + ' ' + textLine.replace('\n', '\n\t') + '\n')

    def load(self, dirPath):
        self.dirPath, self.identifier = os.path.split(dirPath)
        self.data = w.loadFromFile(os.path.join(self.dirPath, self.identifier, self.dataName))

    def editModule(self, treeView):
        w.editModule(os.path.join(self.dirPath, self.identifier, 'global_module.py'))
        
    def getNextId(self):
        id = 99
        def walkChildren(cfgNode):
            nonlocal id
            for child in cfgNode.children:
                id = max(id, child.data.get('id', 0))
                walkChildren(child)
        walkChildren(self)
        return id + 1
    
    def getNodeById(self, id):
        def walkChildren(cfgNode):
            for child in cfgNode.children:
                if child.data.get('id', 0) == id: return child
                cfgNode = walkChildren(child)
                if cfgNode is not None: return cfgNode
        return walkChildren(self)
        
    def getLinkedNodes(self, node):
        'Получить список узлов, которые ссылаются на указанный узел. Т.е. свойство type узла равно id указанного узла.'
        nodesList = []
        id = node.data.get('id', None)
        if id is not None:
            def walkChildren(cfgNode):
                for child in cfgNode.children:
                    if child.data.get('type', None) == id and not self.isSubnode(child, node): 
                        nodesList.append(child)
                    walkChildren(child) # рекурсивно обойти подузлы
            walkChildren(self)            
        return nodesList
        
    def nodePath(self, node):
        _nodePath = node.identifier
        while True:
            node = node.parent
            if not node: break
            _nodePath = node.identifier + '.' + _nodePath
        return _nodePath
        
    def isSubnode(self, nodeChild, nodeParent):
        while True:
            if nodeChild is nodeParent:
                return True
            nodeChild = nodeChild.parent
            if not nodeChild: # добрались до корня дерева
                return False
            

CfgRootNode.createAction('Редактировать глобальный модуль', ':/icons/fugue/script-code.png', CfgRootNode.editModule)
CfgRootNode.createAction('Свойства конфигурации', ':/icons/fugue/property.png', CfgRootNode.edit, True)
