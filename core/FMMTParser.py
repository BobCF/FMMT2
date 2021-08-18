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

    def CompressData(self, TargetTree):
        TreePath = TargetTree.GetTreePath()
        print('TreePath', TreePath)
        pos = len(TreePath)
        print('\npos', pos)
        while pos:
            print(TreePath[pos-1].key)
            if TreePath[pos-1].type == SECTION_TREE and TreePath[pos-1].Data.Type == 0x02:
                self.CompressSectionData(TreePath[pos-1], pos, TreePath[pos-1].Data.ExtHeader.SectionDefinitionGuid)
            else:
                self.CompressSectionData(TreePath[pos-1], pos)
            pos -= 1
            print('\npos', pos)

    def CompressSectionData(self, TargetTree, pos, GuidTool=None):
        NewData = b''
        temp_save_child = TargetTree.Child
        with open('Output\Add_Child_{}.ffs'.format(pos), "wb") as f:
            for item in temp_save_child:
                if item.type == SECTION_TREE and not item.Data.OriData and item.Data.ExtHeader:
                      NewData += struct2stream(item.Data.Header) + struct2stream(item.Data.ExtHeader) + item.Data.Data + item.Data.PadData
                elif item.type == SECTION_TREE and item.Data.OriData and not item.Data.ExtHeader:
                    NewData += struct2stream(item.Data.Header) + item.Data.OriData + item.Data.PadData
                elif item.type == SECTION_TREE and item.Data.OriData and item.Data.ExtHeader:
                    NewData += struct2stream(item.Data.Header) + struct2stream(item.Data.ExtHeader) + item.Data.OriData + item.Data.PadData
                elif item.type == FFS_FREE_SPACE:
                    NewData += item.Data.Data + item.Data.PadData
                else:
                    NewData += struct2stream(item.Data.Header) + item.Data.Data + item.Data.PadData
            f.write(NewData)
        if TargetTree.Data:
            with open('Output\Sec_ori_{}.ffs'.format(pos), "wb") as f:
                f.write(TargetTree.Data.Data)
            print('Ori TargetTree.Data.Data', len(TargetTree.Data.Data))
            TargetTree.Data.Data = NewData
            with open('Output\Sec_new_{}.ffs'.format(pos), "wb") as f:
                f.write(TargetTree.Data.Data)
            print('length of current FinalData\n', len(TargetTree.Data.Data))
        if GuidTool:
            ParPath = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+os.path.sep+"..")
            ToolPath = os.path.join(ParPath, r'FMMTConfig.ini')
            print('GuidTool:',  struct2stream(GuidTool))
            guidtool = GUIDTools(ToolPath).__getitem__(struct2stream(GuidTool))
            print('len(TargetTree.Data.OriData)', len(TargetTree.Data.OriData))
            CompressedData = guidtool.pack(TargetTree.Data.Data)
            print('len(CompressedData)', len(CompressedData))
            if len(CompressedData) < len(TargetTree.Data.OriData):
                size_delta = len(TargetTree.Data.OriData) - len(CompressedData)
                print('TargetTree.Size', hex(TargetTree.Data.Size))
                ChangeSize(TargetTree, size_delta)
                print('Changed TargetTree.Size', hex(TargetTree.Data.Size))
                OriPad_Size = len(TargetTree.Data.PadData)
                NewPad_Size = GetPadSize(TargetTree.Data.Header.SECTION_SIZE, 4)
                TargetTree.Data.PadData = NewPad_Size * b'\x00'
                TargetTree.Data.OriData = CompressedData
                print('len(TargetTree.Data.Data)', len(TargetTree.Data.Data))
                print('len(CompressedData)', len(CompressedData))
                offset_delta = size_delta + OriPad_Size - NewPad_Size
                # while TargetTree.NextRel:
                #     TargetTree.NextRel.Data.HOffset -= offset_delta
                #     TargetTree.NextRel.Data.DOffset -= offset_delta
                #     TargetTree = TargetTree.NextRel
                # TargetTree.Data.PadData += offset_delta * b'\xff'
                Tar_Parent = TargetTree.Parent
                NextFfs = Tar_Parent.NextRel
                print('Tar_Parent', Tar_Parent.Data.Name)
#                 print('NextFfs', NextFfs.Data.Name)
                if NextFfs and NextFfs.type == FFS_PAD:
                    ChangeSize(Tar_Parent, offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta - Tar_Parent_New_Pad + Tar_Parent_Ori_Pad
                    # NextFfs.Data.HOffset -= ffs_offset_delta
                    # NextFfs.Data.DOffset -= ffs_offset_delta
                    # print('NextFfs.Data.HOffset', NextFfs.Data.HOffset)
                    NextFfs.Data.Data += ffs_offset_delta * b'\xff'
                    # NextFfs.Data.Size += ffs_offset_delta
                    ChangeSize(NextFfs, -ffs_offset_delta)
                elif NextFfs and NextFfs.type == FFS_FREE_SPACE:
                    # Tar_Parent.Data.Size -= offset_delta
                    ChangeSize(Tar_Parent, offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta - Tar_Parent_New_Pad + Tar_Parent_Ori_Pad
                    # NextFfs.Data.HOffset -= ffs_offset_delta
                    # NextFfs.Data.DOffset -= ffs_offset_delta
                    NextFfs.Data.Data += ffs_offset_delta * b'\xff'
                else:
                    if Tar_Parent.type == FFS_TREE and offset_delta >= Tar_Parent.Data.Header.HeaderLength:
                        ChangeSize(Tar_Parent, offset_delta)
                        Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                        Tar_Parent_New_Pad = GetPadSize(Tar_Parent.Data.Size, 8)
                        Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                        ffs_offset_delta = offset_delta - Tar_Parent_New_Pad + Tar_Parent_Ori_Pad
                        new_ffs_pad = NODETREE(PADVECTOR)
                        new_ffs_pad.type = FFS_PAD
                        new_ffs_pad.Data = FfsNode(b'\xff'* ffs_offset_delta)
                        new_ffs_pad.Data.Size = ffs_offset_delta
                        ChangeSize(new_ffs_pad)
                        Target_index = Tar_Parent.Parent.Child.index(NextFfs)
                        Tar_Parent.Parent.insertChild(new_ffs_pad, Target_index)
                    else:
                        print('SoSo')
                        TargetTree.Data.PadData += offset_delta * b'\x00'
            elif len(CompressedData) == len(TargetTree.Data.OriData):
                print('Same Length!')
                TargetTree.Data.OriData = CompressedData
            elif len(CompressedData) > len(TargetTree.Data.OriData):
                size_delta = len(CompressedData) - len(TargetTree.Data.OriData)
                ChangeSize(TargetTree, -size_delta)
                OriPad_Size = len(TargetTree.Data.PadData)
                NewPad_Size = GetPadSize(TargetTree.Data.Size, 4)
                TargetTree.Data.PadData = NewPad_Size * b'\x00'
                TargetTree.Data.OriData = CompressedData
                offset_delta = size_delta - OriPad_Size + NewPad_Size
                Tar_Parent = TargetTree.Parent
                NextFfs = Tar_Parent.NextRel
                if NextFfs.type == FFS_FREE_SPACE and offset_delta <= len(NextFfs.Data.Data):
                    # while TargetTree.NextRel:
                    #     TargetTree.NextRel.Data.HOffset += offset_delta
                    #     TargetTree.NextRel.Data.DOffset += offset_delta
                    #     TargetTree = TargetTree.NextRel
                    ChangeSize(Tar_Parent, -offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta + Tar_Parent_New_Pad - Tar_Parent_Ori_Pad
                    # NextFfs.Data.HOffset += ffs_offset_delta
                    # NextFfs.Data.DOffset += ffs_offset_delta
                    NextFfs.Data.Data = (len(NextFfs.Data.Data) - ffs_offset_delta) * b'\xff'
                elif NextFfs.type == FFS_PAD and offset_delta <= NextFfs.Data.Size + len(NextFfs.Data.PadData)- NextFfs.Data.Header.HeaderLength:
                    # while TargetTree.NextRel:
                    #     TargetTree.NextRel.Data.HOffset += offset_delta
                    #     TargetTree.NextRel.Data.DOffset += offset_delta
                    #     TargetTree = TargetTree.NextRel
                    ChangeSize(Tar_Parent, -offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta + Tar_Parent_New_Pad - Tar_Parent_Ori_Pad
                    # NextFfs.Data.HOffset += ffs_offset_delta
                    # NextFfs.Data.DOffset += ffs_offset_delta
                    ChangeSize(NextFfs, ffs_offset_delta)
                    NextFfs.Data.Data = NextFfs.Data.Data[:NextFfs.Data.Size]
                elif NextFfs.type == FFS_PAD and offset_delta <= (NextFfs.Data.Size + len(NextFfs.Data.PadData)):
                    # while TargetTree.NextRel:
                    #     TargetTree.NextRel.Data.HOffset += offset_delta
                    #     TargetTree.NextRel.Data.DOffset += offset_delta
                    #     TargetTree = TargetTree.NextRel
                    ChangeSize(Tar_Parent, -NextFfs.Data.Size)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta + Tar_Parent_New_Pad - Tar_Parent_Ori_Pad
                    NextFfs.Data.Size -= ffs_offset_delta
                    NextFfs.Data.Data = NextFfs.Data.Data[:NextFfs.Data.Size]
                    Tar_Parent.Data.Data += (NextFfs.Data.Size + len(NextFfs.Data.PadData)) * b'\x00'
                    # Tar_Parent.Data.Size += NextFfs.Data.Size + len(NextFfs.Data.PadData)
                    ChangeSize(Tar_Parent, -(NextFfs.Data.Size + len(NextFfs.Data.PadData)))
                    Tar_Parent.Parent.Child.remove(NextFfs)
                else:
                    print('Error Compress! Do not have enough space to store new Compressed data!!')

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
