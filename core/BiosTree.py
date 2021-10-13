## @file
# This file is used to define the Bios layout tree structure and related operations.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
from PI.Common import *

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

class BIOSTREE:
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
    def insertChild(self, newNode, pos=None):
        if len(self.Child) == 0:
            self.Child.append(newNode)
        else:
            if not pos:
                LastTree = self.Child[-1]
                self.Child.append(newNode)
                LastTree.NextRel = newNode
                newNode.LastRel = LastTree
            else:
                newNode.NextRel = self.Child[pos-1].NextRel
                newNode.LastRel = self.Child[pos].LastRel
                self.Child[pos-1].NextRel = newNode
                self.Child[pos].LastRel = newNode
                self.Child.insert(pos, newNode)
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
        if self.key == key or (self.Data and self.Data.Name == key) or (self.type == FFS_TREE and self.Data.UiName == key):
            Findlist.append(self)
        else:
            for item in self.Child:
                item.FindNode(key, Findlist)

    def GetTreePath(self):
        BiosTreePath = [self]
        while self.Parent:
            BiosTreePath.insert(0, self.Parent)
            self = self.Parent
        return BiosTreePath

    def parserTree(self, TreeInfo, space =""):
        if self.type == ROOT_TREE or self.type == ROOT_FV_TREE or self.type == ROOT_FFS_TREE or self.type == ROOT_SECTION_TREE:
            TreeInfo.append("Name:{}  Type:{}  FilesNum:{}".format(self.key, self.type, len(self.Child)))
        elif self.type == FFS_TREE:
            TreeInfo.append("{}Name:{}  UiName:{}  Version:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.Data.UiName, self.Data.Version, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        elif self.type == SECTION_TREE and self.Data.Type == 0x02:
            TreeInfo.append("{}Name:{}  Type:{}  Size:{}  DecompressedSize:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(len(self.Data.OriData)+self.Data.HeaderLength), hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        elif self is not None:
            TreeInfo.append("{}Name:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        space += "  "
        for item in self.Child:
            item.parserTree(TreeInfo, space)
