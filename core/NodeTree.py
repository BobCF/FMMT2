from PI.ExtendCType import *

ROOT_TREE = 'ROOT'
ROOT_FV_TREE = 'ROOT_FV_TREE'
ROOT_FFS_TREE = 'ROOT_FFS_TREE'
ROOT_SECTION_TREE = 'ROOT_SECTION_TREE'

FV_TREE = 'FV'
DATA_FV_TREE = 'DATA_FV'
FFS_TREE = 'FFS'
FFS_PAD = 'FFS_PAD'
FFS_FREE_SPACE = 'FFS_FREE_SPACE'
SECTION_TREE = 'SECTION'
SEC_FV_TREE = 'SEC_FV_IMAGE'
BINARY_DATA = 'BINARY'

class NODETREE:
    def __init__(self, NodeName):
        self.key = NodeName
        self.type = None
        self.Data = None
        self.Child = []
        self.Findlist = []
        self.Parent = None
        self.NextRel = None
        self.LastRel = None
 
    def HasChild(self):
        if self.Child == []:
            return False
        else:
            return True

    def isFinalChild(self):
        ParTree = self.Parent
        if ParTree:
            if ParTree.Child[-1] == self:
                return True
        return False

    # FvTree.insertChild()
    def insertChild(self, newNode, pos=-1):
        if len(self.Child) == 0:
            self.Child.append(newNode)
        else:
            if pos == -1:
                LastTree = self.Child[pos]
                self.Child.append(newNode)
                LastTree.NextRel = newNode
                newNode.LastRel = LastTree
            else:
                self.Child.insert(pos, newNode)
                newNode.NextRel = self.Child[pos-1].NextRel
                newNode.LastRel = self.Child[pos+1].LastRel
                self.Child[pos-1].NextRel = newNode
                self.Child[pos+1].LastRel = newNode
        newNode.Parent = self

    # lastNode.insertRel(newNode)
    def insertRel(self, newNode):
        if self.Parent:
            parentTree = self.Parent
            new_index = parentTree.Child.index(self) + 1
            parentTree.Child.insert(new_index, newNode)
        self.NextRel = newNode
        newNode.LastRel = self

    def deleteNode(self, deletekey):
        FindStatus, DeleteTree = self.FindNode(deletekey)
        print(DeleteTree.key)
        if FindStatus:
            parentTree = DeleteTree.Parent
            lastTree = DeleteTree.LastRel
            nextTree = DeleteTree.NextRel
            if parentTree:
                index = parentTree.Child.index(DeleteTree)
                del parentTree.Child[index]
            if lastTree and nextTree:
                lastTree.NextRel = nextTree
                nextTree.LastRel = lastTree
            elif lastTree:
                lastTree.NextRel = None
            elif nextTree:
                nextTree.LastRel = None
            return DeleteTree
        else:
            print('Could not find the target tree')
            return None

    def FindNode(self, key, Findlist):
        print(self.key, key)
        if self.key == key or (self.Data and self.Data.Name == key) or (self.type == FFS_TREE and self.Data.UiName == key):
            Findlist.append(self)
        else:
            for item in self.Child:
                item.FindNode(key, Findlist)

    def GetTreePath(self):
        NodeTreePath = [self]
        while self.Parent:
            NodeTreePath.insert(0, self.Parent)
            self = self.Parent
        return NodeTreePath

    def parserTree(self, TreeInfo, space =""):
        if self.type == ROOT_TREE or self.type == ROOT_FV_TREE or self.type == ROOT_FFS_TREE or self.type == ROOT_SECTION_TREE:
            print("Name:{}  Type:{}  FilesNum:{}".format(self.key, self.type, len(self.Child)))
            TreeInfo.append("Name:{}  Type:{}  FilesNum:{}".format(self.key, self.type, len(self.Child)))
        elif self.type == FFS_TREE:
            print("{}Name:{}  UiName:{}  Version:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.Data.UiName, self.Data.Version, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
            TreeInfo.append("{}Name:{}  UiName:{}  Version:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.Data.UiName, self.Data.Version, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        elif self.type == SECTION_TREE and self.Data.Type == 0x02:
            print("{}Name:{}  Type:{}  Size:{}  DecompressedSize:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(len(self.Data.OriData)), hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
            TreeInfo.append("{}Name:{}  Type:{}  Size:{}  DecompressedSize:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(len(self.Data.OriData)), hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        elif self is not None:
            print("{}Name:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
            TreeInfo.append("{}Name:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        space += "  "
        for item in self.Child:
            item.parserTree(TreeInfo, space)
