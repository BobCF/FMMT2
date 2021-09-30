## @file
# This file is used to parser the image as a tree.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent

##
from PI.ExtendCType import *
from PI.Common import *
from core.BinaryFactoryProduct import ParserEntry
from core.NodeClass import *
from core.NodeTree import *
from core.GuidTools import *

class FMMTParser:
    def __init__(self, name, TYPE):
        self.WholeFvTree = NODETREE(name)
        self.WholeFvTree.type = TYPE
        self.FinalData = b''
        self.BinaryInfo = []

    ## Parser the nodes in WholeTree.
    def ParserFromRoot(self, WholeFvTree=None, whole_data=b'', Reloffset = 0):
        if WholeFvTree.type == ROOT_TREE or WholeFvTree.type == ROOT_FV_TREE:
            print('ROOT Tree: ', WholeFvTree.type)
            ParserEntry().DataParser(self.WholeFvTree, whole_data, Reloffset)
        else:
            ParserEntry().DataParser(WholeFvTree, whole_data, Reloffset)
        for Child in WholeFvTree.Child:
            self.ParserFromRoot(Child, "")

    def Encapsulation(self, rootTree, CompressStatus):
        if rootTree.type == ROOT_TREE or rootTree.type == ROOT_FV_TREE or rootTree.type == ROOT_FFS_TREE or rootTree.type == ROOT_SECTION_TREE:
            print('Start at Root !!')
        elif rootTree.type == BINARY_DATA or rootTree.type == FFS_FREE_SPACE:
            self.FinalData += rootTree.Data.Data
            rootTree.Child = []
        elif rootTree.type == DATA_FV_TREE or rootTree.type == FFS_PAD:
            print('Encapsulation leaf DataFv/FfsPad - {} Data'.format(rootTree.key))
            self.FinalData += struct2stream(rootTree.Data.Header) + rootTree.Data.Data + rootTree.Data.PadData
            if rootTree.isFinalChild():
                ParTree = rootTree.Parent
                if ParTree.type != 'ROOT':
                    self.FinalData += ParTree.Data.PadData
            rootTree.Child = []
        elif rootTree.type == FV_TREE or rootTree.type == FFS_TREE or rootTree.type == SEC_FV_TREE:
            if rootTree.HasChild():
                print('Encapsulation Encap Fv/Ffs- {}'.format(rootTree.key))
                self.FinalData += struct2stream(rootTree.Data.Header)
            else:
                print('Encapsulation leaf Fv/Ffs - {} Data'.format(rootTree.key))
                self.FinalData += struct2stream(rootTree.Data.Header) + rootTree.Data.Data + rootTree.Data.PadData
                if rootTree.isFinalChild():
                    ParTree = rootTree.Parent
                    if ParTree.type != 'ROOT':
                        self.FinalData += ParTree.Data.PadData
        elif rootTree.type == SECTION_TREE:
            # Not compressed section
            if rootTree.Data.OriData == b'' or (rootTree.Data.OriData != b'' and CompressStatus):
                if rootTree.HasChild():
                    if rootTree.Data.ExtHeader:
                        self.FinalData += struct2stream(rootTree.Data.Header) + struct2stream(rootTree.Data.ExtHeader)
                    else:
                        self.FinalData += struct2stream(rootTree.Data.Header)
                else:
                    Data = rootTree.Data.Data
                    if rootTree.Data.ExtHeader:
                        self.FinalData += struct2stream(rootTree.Data.Header) + struct2stream(rootTree.Data.ExtHeader) + Data + rootTree.Data.PadData
                    else:
                        self.FinalData += struct2stream(rootTree.Data.Header) + Data + rootTree.Data.PadData
                    if rootTree.isFinalChild():
                        ParTree = rootTree.Parent
                        self.FinalData += ParTree.Data.PadData
            # If compressed section
            else:
                Data = rootTree.Data.OriData
                rootTree.Child = []
                if rootTree.Data.ExtHeader:
                    self.FinalData += struct2stream(rootTree.Data.Header) + struct2stream(rootTree.Data.ExtHeader) + Data + rootTree.Data.PadData
                else:
                    self.FinalData += struct2stream(rootTree.Data.Header) + Data + rootTree.Data.PadData
                if rootTree.isFinalChild():
                    ParTree = rootTree.Parent
                    self.FinalData += ParTree.Data.PadData
        for Child in rootTree.Child:
            self.Encapsulation(Child, CompressStatus)
