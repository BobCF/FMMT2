## @file
# This file is used to parser the image as a tree.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent

##
from PI.FvHeader import *
from PI.FfsFileHeader import *
from PI.SectionHeader import *
from PI.CommonType import *
from core.GuidTools import *
from ctypes import *
import uuid
import copy

EFI_FIRMWARE_FILE_SYSTEM2_GUID = uuid.UUID("8c8ce578-8a3d-4f1c-9935-896185c32dd3")
EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE = b'x\xe5\x8c\x8c=\x8a\x1cO\x995\x89a\x85\xc3-\xd3'
# EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE = EFI_FIRMWARE_FILE_SYSTEM2_GUID.bytes
EFI_FIRMWARE_FILE_SYSTEM3_GUID = uuid.UUID("5473C07A-3DCB-4dca-BD6F-1E9689E7349A")
# EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE = b'x\xe5\x8c\x8c=\x8a\x1cO\x995\x89a\x85\xc3-\xd3'
EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE = b'z\xc0sT\xcb=\xcaM\xbdo\x1e\x96\x89\xe74\x9a'
EFI_SYSTEM_NVDATA_FV_GUID = uuid.UUID("fff12b8d-7696-4c8b-a985-2747075b4f50")
EFI_SYSTEM_NVDATA_FV_GUID_BYTE = b"\x8d+\xf1\xff\x96v\x8bL\xa9\x85'G\x07[OP"
EFI_FFS_VOLUME_TOP_FILE_GUID = uuid.UUID("1ba0062e-c779-4582-8566-336ae8f78f09")
EFI_FFS_VOLUME_TOP_FILE_GUID_BYTE = b'.\x06\xa0\x1by\xc7\x82E\x85f3j\xe8\xf7\x8f\t'
ZEROVECTOR_BYTE = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
PADVECTOR = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
FVH_SIGNATURE = b'_FVH'


'''       
0x03:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_DISPOSABLE
0x10:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_PE32
0x11:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_PIC
0x12:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_TE
0x13:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_DXE_DEPEX
0x16:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_COMPATIBILITY16
0x17:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_FIRMWARE_VOLUME_IMAGE
0x19:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_RAW
0x1B:EFI_COMMON_SECTION_HEADER,    # EFI_SECTION_PEI_DEPEX
0x1C:EFI_COMMON_SECTION_HEADER     # EFI_SECTION_MM_DEPEX
'''

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

SectionHeaderType = {
    0x01:'EFI_COMPRESSION_SECTION',
    0x02:'EFI_GUID_DEFINED_SECTION',
    0x03:'EFI_SECTION_DISPOSABLE',
    0x10:'EFI_SECTION_PE32',
    0x11:'EFI_SECTION_PIC',
    0x12:'EFI_SECTION_TE',
    0x13:'EFI_SECTION_DXE_DEPEX',
    0x14:'EFI_SECTION_VERSION',
    0x15:'EFI_SECTION_USER_INTERFACE',
    0x16:'EFI_SECTION_COMPATIBILITY16',
    0x17:'EFI_SECTION_FIRMWARE_VOLUME_IMAGE',
    0x18:'EFI_FREEFORM_SUBTYPE_GUID_SECTION',
    0x19:'EFI_SECTION_RAW',
    0x1B:'EFI_SECTION_PEI_DEPEX',
    0x1C:'EFI_SECTION_MM_DEPEX'
}    
# SectionHeaderType = [0x01, 0x02, 0x03, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1B, 0x1C]
HeaderType = [0x01, 0x02, 0x14, 0x15, 0x18]
# HeaderType = [0x01, 0x02, 0x18]

# Section_Count = 0
Fv_count = 0
VTF_index = 0

class BinaryNode:
    def __init__(self, name):
        self.Size = 0
        self.Name = "BINARY" + str(name)
        self.HOffset = 0
        self.Data = b''

class FvNode:
    def __init__(self, name, buffer: bytes):
        self.Header = EFI_FIRMWARE_VOLUME_HEADER.from_buffer_copy(buffer)
        Map_num = (self.Header.HeaderLength - 56)//8
        self.Header = Refine_FV_Header(Map_num).from_buffer_copy(buffer)
        self.Name = "FV" + str(name)
        if self.Header.ExtHeaderOffset:
            self.ExtHeader = EFI_FIRMWARE_VOLUME_EXT_HEADER.from_buffer_copy(buffer[self.Header.ExtHeaderOffset:])
            self.Name =  uuid.UUID(bytes_le=struct2stream(self.ExtHeader.FvName))
        self.Size = self.Header.FvLength
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        if self.Header.Signature != b'_FVH':
            print('Error Fv Header!!')
        self.PadData = b''

    def ModCheckSum(self):
        pass

class FfsNode:
    def __init__(self, buffer: bytes):
        self.Attributes = unpack("<B", buffer[19:20])[0]
        if self.Attributes != 0x01:
            self.Header = EFI_FFS_FILE_HEADER.from_buffer_copy(buffer)
        else:
            self.Header = EFI_FFS_FILE_HEADER2.from_buffer_copy(buffer)
        self.Name = uuid.UUID(bytes_le=struct2stream(self.Header.Name))
        self.Size = self.Header.FFS_FILE_SIZE
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        self.PadData = b''

    def ModCheckSum(self):
        HeaderData = struct2stream(self.Header)
        HeaderSum = 0
        DataSum = 0
        if self.Header.Attributes != '0x00':
            for item in self.Data:
                DataSum += item
            if hex(DataSum + self.Header.IntegrityCheck.Checksum.File)[-2:] != '00':
                self.Header.IntegrityCheck.Checksum.File == 0x100 - int(hex(DataSum)[-2:], 16)
        else:
            self.Header.IntegrityCheck.Checksum.File =='0xAA'
        for item in HeaderData:
            HeaderSum += item
        HeaderSum -= self.Header.State
        HeaderSum -= self.Header.IntegrityCheck.Checksum.File
        if hex(HeaderSum)[-2:] != '00':
            self.Header.IntegrityCheck.Checksum.Header == 0x100 - int(hex(HeaderSum)[-2:], 16)

class SectionNode:
    def __init__(self, buffer: bytes):
        if buffer[0:3] != b'\xff\xff\xff':
            self.Header = EFI_COMMON_SECTION_HEADER.from_buffer_copy(buffer)
        else:
            self.Header = EFI_COMMON_SECTION_HEADER2.from_buffer_copy(buffer)
        if self.Header.Type in SectionHeaderType:
            self.Name = SectionHeaderType[self.Header.Type]
        elif self.Header.Type == 0:
            self.Name = "EFI_SECTION_RAW"
        else:
            self.Name = "SECTION"
        if self.Header.Type in HeaderType:
            self.ExtHeader = self.GetExtHeader(self.Header.Type, buffer[self.Header.Common_Header_Size():])
            self.HeaderLength = self.Header.Common_Header_Size() + self.ExtHeader.ExtHeaderSize()
        else:
            self.ExtHeader = None
            self.HeaderLength = self.Header.Common_Header_Size()
        self.Size = self.Header.SECTION_SIZE
        self.Type = self.Header.Type
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        self.OriData = b''
        self.OriHeader = b''
        self.PadData = b''

    def GetExtHeader(self, Type, buffer:bytes):
        if Type == 0x01:
            return EFI_COMPRESSION_SECTION.from_buffer_copy(buffer)
        elif Type == 0x02:
            return EFI_GUID_DEFINED_SECTION.from_buffer_copy(buffer)
        elif Type == 0x14:
            return EFI_SECTION_VERSION.from_buffer_copy(buffer)
        elif Type == 0x15:
            return EFI_SECTION_USER_INTERFACE.from_buffer_copy(buffer)
        elif Type == 0x18:
            return EFI_FREEFORM_SUBTYPE_GUID_SECTION.from_buffer_copy(buffer)

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

    def GetTreePath(self):
        NodeTreePath = [self]
        while self.Parent:
            NodeTreePath.insert(0, self.Parent)
            self = self.Parent
        return NodeTreePath

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

    def parserTree(self, TreeInfo, space =""):
        if self.type == ROOT_TREE or self.type == ROOT_FV_TREE or self.type == ROOT_FFS_TREE or self.type == ROOT_SECTION_TREE:
            print("Name:{}  Type:{}  FilesNum:{}".format(self.key, self.type, len(self.Child)))
            TreeInfo.append("Name:{}  Type:{}  FilesNum:{}".format(self.key, self.type, len(self.Child)))
        elif self is not None:
            print("{}Name:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
            TreeInfo.append("{}Name:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.Data.Name, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        space += "  "
        for item in self.Child:
            item.parserTree(TreeInfo, space)

    def isFinalChild(self):
        ParTree = self.Parent
        if ParTree:
            if ParTree.Child[-1] == self:
                return True
        return False

    def FindNode(self, key, Findlist):
        print(self.key, key)
        if self.key == key or (self.Data and self.Data.Name == key):
            Findlist.append(self)
        else:
            for item in self.Child:
                item.FindNode(key, Findlist)

class FMMTParser:
    def __init__(self, name, TYPE):
        self.WholeFvTree = NODETREE(name)
        self.WholeFvTree.type = TYPE
        self.FinalData = b''
        self.BinaryInfo = []

    def GetPadSize(self, Size, alignment):
        if Size % alignment == 0:
            return 0
        Pad_Size = alignment - Size % alignment
        return Pad_Size

    def ChangeSize(self, TargetTree, size_delta = 0):
        if type(TargetTree.Data.Header) == type(EFI_FFS_FILE_HEADER2) or type(TargetTree.Data.Header) == type(EFI_COMMON_SECTION_HEADER2): 
            TargetTree.Data.Size -= size_delta
            TargetTree.Data.Header.ExtendedSize -= size_delta 
        else:
            TargetTree.Data.Size -= size_delta
            TargetTree.Data.Header.Size[0] = TargetTree.Data.Size % (16**2)
            TargetTree.Data.Header.Size[1] = TargetTree.Data.Size % (16**4) //(16**2)
            TargetTree.Data.Header.Size[2] = TargetTree.Data.Size // (16**4)

    def ReCompressed(self, TargetTree):
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
                if item.type == SECTION_TREE and item.Data.ExtHeader:
                    f.write(struct2stream(item.Data.Header)+ struct2stream(item.Data.ExtHeader) + item.Data.Data + item.Data.PadData)
                    NewData += struct2stream(item.Data.Header) + struct2stream(item.Data.ExtHeader) + item.Data.Data + item.Data.PadData
                else:
                    f.write(struct2stream(item.Data.Header) + item.Data.Data + item.Data.PadData)
                    NewData += struct2stream(item.Data.Header) + item.Data.Data + item.Data.PadData
        if TargetTree.Data:
            with open('Output\Sec_ori_{}.ffs'.format(pos), "wb") as f:
                f.write(TargetTree.Data.Data)           
            print('Ori TargetTree.Data.Data', len(TargetTree.Data.Data))
            TargetTree.Data.Data = NewData
            with open('Output\Sec_new_{}.ffs'.format(pos), "wb") as f:
                f.write(TargetTree.Data.Data)
            print('length of current FinalData\n', len(TargetTree.Data.Data))
        if GuidTool:
            guidtool = GUIDTools(r'FMMTConfig.ini').__getitem__(GuidTool)
            print('len(TargetTree.Data.OriData)', len(TargetTree.Data.OriData))
            CompressedData = guidtool.pack(TargetTree.Data.Data)

            if len(CompressedData) < len(TargetTree.Data.OriData):
                size_delta = len(TargetTree.Data.OriData) - len(CompressedData)
                print('TargetTree.Size', hex(TargetTree.Data.Size))
                self.ChangeSize(TargetTree, size_delta)
                print('Changed TargetTree.Size', hex(TargetTree.Data.Size))
                OriPad_Size = len(TargetTree.Data.PadData)
                NewPad_Size = self.GetPadSize(TargetTree.Data.Size, 4)
                TargetTree.Data.PadData = NewPad_Size * b'\x00'
                TargetTree.Data.OriData = CompressedData
                print('len(TargetTree.Data.Data)', len(TargetTree.Data.Data))
                print('len(CompressedData)', len(CompressedData))
                offset_delta = size_delta + OriPad_Size - NewPad_Size
                while TargetTree.NextRel:
                    TargetTree.NextRel.Data.HOffset -= offset_delta
                    TargetTree.NextRel.Data.DOffset -= offset_delta
                    TargetTree = TargetTree.NextRel
                # TargetTree.Data.PadData += offset_delta * b'\xff'
                Tar_Parent = TargetTree.Parent
                NextFfs = Tar_Parent.NextRel
                print('Tar_Parent', Tar_Parent.Data.Name)
                print('NextFfs', NextFfs.Data.Name)
                if NextFfs.type == FFS_PAD:
                    self.ChangeSize(Tar_Parent, offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = self.GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta - Tar_Parent_New_Pad + Tar_Parent_Ori_Pad
                    NextFfs.Data.HOffset -= ffs_offset_delta
                    NextFfs.Data.DOffset -= ffs_offset_delta
                    print('NextFfs.Data.HOffset', NextFfs.Data.HOffset)
                    NextFfs.Data.Data += ffs_offset_delta * b'\xff'
                    # NextFfs.Data.Size += ffs_offset_delta
                    self.ChangeSize(NextFfs, -ffs_offset_delta)
                elif NextFfs.type == FFS_FREE_SPACE:
                    # Tar_Parent.Data.Size -= offset_delta
                    self.ChangeSize(Tar_Parent, offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = self.GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta - Tar_Parent_New_Pad + Tar_Parent_Ori_Pad
                    NextFfs.Data.HOffset -= ffs_offset_delta
                    NextFfs.Data.DOffset -= ffs_offset_delta
                    NextFfs.Data.Data += ffs_offset_delta * b'\xff'
                else:
                    if offset_delta >= Tar_Parent.Data.Header.HeaderLength:
                        self.ChangeSize(Tar_Parent, offset_delta)
                        Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                        Tar_Parent_New_Pad = self.GetPadSize(Tar_Parent.Data.Size, 8)
                        Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                        ffs_offset_delta = offset_delta - Tar_Parent_New_Pad + Tar_Parent_Ori_Pad
                        new_ffs_pad = NODETREE(PADVECTOR)
                        new_ffs_pad.type = FFS_PAD
                        new_ffs_pad.Data = FfsNode(b'\xff'* ffs_offset_delta)
                        new_ffs_pad.Data.Size = ffs_offset_delta
                        self.ChangeSize(new_ffs_pad)
                        Target_index = Tar_Parent.Parent.Child.index(NextFfs)
                        Tar_Parent.Parent.insertChild(new_ffs_pad, Target_index)
                    else:
                        TargetTree.Data.PadData += offset_delta * b'\x00'
            elif len(CompressedData) > len(TargetTree.Data.OriData):
                size_delta = len(CompressedData) - len(TargetTree.Data.OriData)
                self.ChangeSize(TargetTree, -size_delta)
                OriPad_Size = len(TargetTree.Data.PadData)
                NewPad_Size = self.GetPadSize(TargetTree.Data.Size, 4)
                TargetTree.Data.PadData = NewPad_Size * b'\x00'
                TargetTree.Data.OriData = CompressedData
                offset_delta = size_delta - OriPad_Size + NewPad_Size
                Tar_Parent = TargetTree.Parent
                NextFfs = Tar_Parent.NextRel
                if NextFfs.type == FFS_FREE_SPACE and offset_delta <= len(NextFfs.Data.Data):
                    while TargetTree.NextRel:
                        TargetTree.NextRel.Data.HOffset += offset_delta
                        TargetTree.NextRel.Data.DOffset += offset_delta
                        TargetTree = TargetTree.NextRel
                    self.ChangeSize(Tar_Parent, -offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = self.GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta + Tar_Parent_New_Pad - Tar_Parent_Ori_Pad
                    NextFfs.Data.HOffset += ffs_offset_delta
                    NextFfs.Data.DOffset += ffs_offset_delta
                    NextFfs.Data.Data = (len(NextFfs.Data.Data) - ffs_offset_delta) * b'\xff'
                elif NextFfs.type == FFS_PAD and offset_delta <= NextFfs.Data.Size + len(NextFfs.Data.PadData)- NextFfs.Data.Header.HeaderLength:
                    while TargetTree.NextRel:
                        TargetTree.NextRel.Data.HOffset += offset_delta
                        TargetTree.NextRel.Data.DOffset += offset_delta
                        TargetTree = TargetTree.NextRel
                    self.ChangeSize(Tar_Parent, -offset_delta)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = self.GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta + Tar_Parent_New_Pad - Tar_Parent_Ori_Pad
                    NextFfs.Data.HOffset += ffs_offset_delta
                    NextFfs.Data.DOffset += ffs_offset_delta
                    self.ChangeSize(NextFfs, ffs_offset_delta)
                    NextFfs.Data.Data = NextFfs.Data.Data[:NextFfs.Data.Size]
                elif NextFfs.type == FFS_PAD and offset_delta <= (NextFfs.Data.Size + len(NextFfs.Data.PadData)):
                    while TargetTree.NextRel:
                        TargetTree.NextRel.Data.HOffset += offset_delta
                        TargetTree.NextRel.Data.DOffset += offset_delta
                        TargetTree = TargetTree.NextRel
                    self.ChangeSize(Tar_Parent, -NextFfs.Data.Size)
                    Tar_Parent_Ori_Pad = len(Tar_Parent.Data.PadData)
                    Tar_Parent_New_Pad = self.GetPadSize(Tar_Parent.Data.Size, 8)
                    Tar_Parent.Data.PadData =  Tar_Parent_New_Pad * b'\xff'
                    ffs_offset_delta = offset_delta + Tar_Parent_New_Pad - Tar_Parent_Ori_Pad
                    NextFfs.Data.Size -= ffs_offset_delta
                    NextFfs.Data.Data = NextFfs.Data.Data[:NextFfs.Data.Size]
                    Tar_Parent.Data.Data += (NextFfs.Data.Size + len(NextFfs.Data.PadData)) * b'\x00'
                    # Tar_Parent.Data.Size += NextFfs.Data.Size + len(NextFfs.Data.PadData)
                    self.ChangeSize(Tar_Parent, -(NextFfs.Data.Size + len(NextFfs.Data.PadData)))
                    Tar_Parent.Parent.Child.remove(NextFfs)
                else:
                    print('Error Compress! Do not have enough space to store new Compressed data!!')

    ## Use GuidTool to decompress data.
    def DeCompressData(self, GuidTool, Section_Data):
        guidtool = GUIDTools(r'FMMTConfig.ini').__getitem__(struct2stream(GuidTool))
        DecompressedData = guidtool.unpack(Section_Data)
        return DecompressedData

    ## Decompress the compressed section.
    def ParserSection(self, Section_Tree):
        print("Start DeCompressSection")
        print(Section_Tree.Data.Type)
        if Section_Tree.Data.Type == 0x01:
            Section_Tree.Data.OriData = Section_Tree.Data.Data
            self.ParserFfs(Section_Tree, b'')
        elif Section_Tree.Data.Type == 0x02:
            print("GuidTool*************************************************")
            Section_Tree.Data.OriData = Section_Tree.Data.Data
            DeCompressGuidTool = Section_Tree.Data.ExtHeader.SectionDefinitionGuid
            Section_Tree.Data.Data = self.DeCompressData(DeCompressGuidTool, Section_Tree.Data.Data)
            Section_Tree.Data.Size = len(Section_Tree.Data.Data) + Section_Tree.Data.HeaderLength
            print('\n      Size of Data Decompressed: {}!'.format(len(Section_Tree.Data.Data)))
            print('      Data Decompressed!')
            self.ParserFfs(Section_Tree, b'')
        elif Section_Tree.Data.Type == 0x03:
            Section_Tree.Data.OriData = Section_Tree.Data.Data
            # Section_Tree.Data.Data = self.Decompress(Section_Tree.Data.Data)
            self.ParserFfs(Section_Tree, b'')
        elif Section_Tree.Data.Type == 0x17:
            print("SecFV*************************************************")
            Sec_Fv_Info = FvNode(Fv_count, Section_Tree.Data.Data)
            Sec_Fv_Tree = NODETREE('FV'+ str(Fv_count))
            Sec_Fv_Tree.type = SEC_FV_TREE
            Sec_Fv_Tree.Data = Sec_Fv_Info
            Sec_Fv_Tree.Data.HOffset = Section_Tree.Data.DOffset
            Sec_Fv_Tree.Data.DOffset = Sec_Fv_Tree.Data.HOffset + Sec_Fv_Tree.Data.Header.HeaderLength
            Sec_Fv_Tree.Data.Data = Section_Tree.Data.Data[Sec_Fv_Tree.Data.Header.HeaderLength:]
            Section_Tree.insertChild(Sec_Fv_Tree)

    # ParserFFs / GetSection
    def ParserFfs(self, ParTree, Whole_Data, Rel_Whole_Offset = 0):
        print('\nParserFfs Start!')
        print('{} - Section '.format(ParTree.key))
        # Section_Count = 0
        Rel_Offset = 0
        Section_Offset = 0
        if ParTree.Data != None:
            Data_Size = len(ParTree.Data.Data)
            Section_Offset = ParTree.Data.DOffset
            Whole_Data = ParTree.Data.Data
        else:
            Data_Size = len(Whole_Data)
        print('  Ffs Data_Size', Data_Size)
        print('  Ffs Data Offset', Section_Offset)
        # print('  Ffs Header Offset', ParTree.Data.HOffset)
        while Rel_Offset < Data_Size:
            print('  Rel_Offset', Rel_Offset)
            Section_Info = SectionNode(Whole_Data[Rel_Offset:])
            # Section_Info = SectionNode(Section_Count, Whole_Data[Rel_Offset:])
            Section_Tree = NODETREE(Section_Info.Name)
            print('      GetSection: ', Section_Info.Name)
            Section_Tree.type = SECTION_TREE
            Section_Tree.Data = Section_Info
            Section_Data = Whole_Data[Rel_Offset+Section_Tree.Data.HeaderLength: Rel_Offset+Section_Tree.Data.Size]
            Section_Tree.Data.DOffset = Section_Offset + Section_Tree.Data.HeaderLength + Rel_Whole_Offset
            print('      Section RelDataRange:', Rel_Offset+Section_Tree.Data.HeaderLength, Rel_Offset+Section_Tree.Data.Size)
            print('      Section DataRange:', Section_Offset+Section_Tree.Data.HeaderLength, Section_Offset+Section_Tree.Data.Size)
            print('      Section_Tree.Data.Header.Type', Section_Tree.Data.Header.Type)
            print('      Section_Tree.Data.Header.Common_Header_Size', Section_Tree.Data.Header.Common_Header_Size())
            
            Section_Tree.Data.HOffset = Section_Offset + Rel_Whole_Offset
            Section_Tree.Data.ROffset = Rel_Offset
            Section_Tree.Data.Data = Section_Data
            print('      Section_Tree.Data.Data length', len(Section_Tree.Data.Data))
            print('      Section_Tree.Data.Size', Section_Tree.Data.Size)
            if Section_Tree.Data.Header.Type == 0:
                print('Ffs Finished!')
                break
            Pad_Size = 0
            if (Rel_Offset+Section_Tree.Data.HeaderLength+len(Section_Tree.Data.Data) != Data_Size):
                Pad_Size = self.GetPadSize(Section_Tree.Data.Size, 4)
                Section_Tree.Data.PadData = Pad_Size * b'\x00'
                print('      Add PadDataSize: ', Pad_Size)
            
            print("**************************OriType", Section_Tree.Data.Header.Type)
            if Section_Tree.Data.Header.Type == 0x02:
                Section_Tree.Data.DOffset = Section_Offset + Section_Tree.Data.ExtHeader.DataOffset + Rel_Whole_Offset
                Section_Tree.Data.Data = Whole_Data[Rel_Offset+Section_Tree.Data.ExtHeader.DataOffset: Rel_Offset+Section_Tree.Data.Size]
                print('      Section_Tree.Data.DOffset', Section_Tree.Data.DOffset)
                print('      Section_Tree.Data.ExtHeader.DataOffset', Section_Tree.Data.ExtHeader.DataOffset)

            Section_Offset += Section_Tree.Data.Size + Pad_Size
            Rel_Offset += Section_Tree.Data.Size + Pad_Size
            # if Section_Tree.Data.HeaderLength + len(Section_Tree.Data.Data) != Data_Size:
            ParTree.insertChild(Section_Tree)

    ##  ParserFv / GetFfs
    def ParserFv(self, ParTree, Whole_Data, Rel_Whole_Offset = 0):
        print('\nParserFv Start!')
        print('{} - Ffs '.format(ParTree.key))
        Ffs_Offset = 0
        Rel_Offset = 0
        # Get the Data from parent tree, if do not have the tree then get it from the whole_data.
        if ParTree.Data != None:
            Data_Size = len(ParTree.Data.Data)
            Ffs_Offset = ParTree.Data.DOffset
            Whole_Data = ParTree.Data.Data
        else:
            Data_Size = len(Whole_Data)
        # Parser all the data to collect all the Ffs recorded in Fv.
        while Rel_Offset < Data_Size:
            # Create a FfsNode and set it as the FFsTree's Data 
            Ffs_Info = FfsNode(Whole_Data[Rel_Offset:])
            Ffs_Tree = NODETREE(Ffs_Info.Name)
            Ffs_Tree.Data = Ffs_Info
            Ffs_Tree.Data.HOffset = Ffs_Offset + Rel_Whole_Offset
            Ffs_Tree.Data.DOffset = Ffs_Offset + Ffs_Tree.Data.Header.HeaderLength + Rel_Whole_Offset
            Ffs_Tree.Data.ROffset = Rel_Offset
            if Ffs_Info.Name == PADVECTOR:
                Ffs_Tree.type = FFS_PAD
                Ffs_Tree.Data.Data = Whole_Data[Rel_Offset+Ffs_Tree.Data.Header.HeaderLength: Rel_Offset+Ffs_Tree.Data.Size]
                Ffs_Tree.Data.Size = len(Ffs_Tree.Data.Data) + Ffs_Tree.Data.Header.HeaderLength
                # if current Ffs is the final ffs of Fv and full of b'\xff', define it with Free_Space
                if struct2stream(Ffs_Tree.Data.Header).replace(b'xff', b'') == b'':
                    Ffs_Tree.type = FFS_FREE_SPACE
                    Ffs_Tree.Data.Data = Whole_Data[Rel_Offset:]
            else:
                Ffs_Tree.type = FFS_TREE
                Ffs_Tree.Data.Data = Whole_Data[Rel_Offset+Ffs_Tree.Data.Header.HeaderLength: Rel_Offset+Ffs_Tree.Data.Size]
            # The final Ffs in Fv does not need to add padding, else must be 8-bytes align with Fv start offset
            Pad_Size = 0
            if Ffs_Tree.type != FFS_FREE_SPACE and (Rel_Offset+Ffs_Tree.Data.Header.HeaderLength+len(Ffs_Tree.Data.Data) != Data_Size):  
                Pad_Size = self.GetPadSize(Ffs_Tree.Data.Size, 8)
                Ffs_Tree.Data.PadData = Pad_Size * b'\xff'
                print('  Add PadDataSize:{} PadData:{} '.format(Pad_Size, Ffs_Tree.Data.PadData))

            Ffs_Offset += Ffs_Tree.Data.Size + Pad_Size
            Rel_Offset += Ffs_Tree.Data.Size + Pad_Size
            # if Ffs_Tree.Data.Header.HeaderLength + len(Ffs_Tree.Data.Data) != Data_Size:
            ParTree.insertChild(Ffs_Tree)
            print('  GetFfs: ', Ffs_Info.Name)
            print('   GetFfsSize: ', Ffs_Tree.Data.Size)
            print('   GetFfsHOffset: ', Ffs_Tree.Data.HOffset)
            print('   GetFfsDOffset: ', Ffs_Tree.Data.DOffset)
            print('   RelOffset', Rel_Offset)
            print('   Data_Size', Data_Size)

    ## Get the first level Fv from Fd file.
    def GetFvFromFd(self, whole_data=b''):
        global VTF_index
        Fd_Struct = []
        data_size = len(whole_data)
        cur_index = 0
        # Get all the EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE FV image offset and length.
        while cur_index < data_size:
            if EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE in whole_data[cur_index:]:
                target_index = whole_data[cur_index:].index(EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE) + cur_index
                if whole_data[target_index+24:target_index+28] == FVH_SIGNATURE and whole_data[target_index-16:target_index] == ZEROVECTOR_BYTE:
                    Fd_Struct.append([FV_TREE, target_index - 16, unpack("Q", whole_data[target_index+16:target_index+24])])
                    cur_index = Fd_Struct[-1][1] + Fd_Struct[-1][2][0]
                else:
                    cur_index = target_index + 16
            else:
                cur_index = data_size
        cur_index = 0
        # Get all the EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE FV image offset and length.
        while cur_index < data_size:
            if EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE in whole_data[cur_index:]:
                target_index = whole_data[cur_index:].index(EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE) + cur_index
                print(EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE, target_index)
                if whole_data[target_index+24:target_index+28] == FVH_SIGNATURE and whole_data[target_index-16:target_index] == ZEROVECTOR_BYTE:
                    Fd_Struct.append([FV_TREE, target_index - 16, unpack("Q", whole_data[target_index+16:target_index+24])])
                    cur_index = Fd_Struct[-1][1] + Fd_Struct[-1][2][0]
                else:
                    cur_index = target_index + 16
            else:
                cur_index = data_size
        cur_index = 0
        # Get all the EFI_SYSTEM_NVDATA_FV_GUID_BYTE FV image offset and length.
        while cur_index < data_size:
            if EFI_SYSTEM_NVDATA_FV_GUID_BYTE in whole_data[cur_index:]:
                target_index = whole_data[cur_index:].index(EFI_SYSTEM_NVDATA_FV_GUID_BYTE) + cur_index
                if whole_data[target_index+24:target_index+28] == FVH_SIGNATURE and whole_data[target_index-16:target_index] == ZEROVECTOR_BYTE:
                    Fd_Struct.append([DATA_FV_TREE, target_index - 16, unpack("Q", whole_data[target_index+16:target_index+24])])
                    cur_index = Fd_Struct[-1][1] + Fd_Struct[-1][2][0]
                else:
                    cur_index = target_index + 16
            else:
                cur_index = data_size
        if EFI_FFS_VOLUME_TOP_FILE_GUID_BYTE in whole_data:
            VTF_index = whole_data.index(EFI_FFS_VOLUME_TOP_FILE_GUID_BYTE)
        # Sort all the collect Fv image with offset.
        Fd_Struct.sort(key=lambda x:x[1])
        tmp_struct = copy.deepcopy(Fd_Struct)
        tmp_index = 0
        Fv_num = len(Fd_Struct)
        # Remove the Fv image included in another Fv image.
        for i in range(1,Fv_num):
            if tmp_struct[i][1]+tmp_struct[i][2][0] < tmp_struct[i-1][1]+tmp_struct[i-1][2][0]:
                Fd_Struct.remove(Fd_Struct[i-tmp_index])
                tmp_index += 1
        print(Fd_Struct)
        return Fd_Struct

    ## Create DataTree with first level /fv Info, then parser each Fv.
    def ParserData(self, whole_data=b'', offset = 0):
        # Get all Fv image in Fd with offset and length
        Fd_Struct = self.GetFvFromFd(whole_data)
        print('Fd_Struct', Fd_Struct)
        data_size = len(whole_data)
        Binary_count = 0
        global Fv_count
        # If the first Fv image is the Binary Fv, add it into the tree. 
        if Fd_Struct[0][1] != 0:
            Binary_node = NODETREE('BINARY'+ str(Binary_count))
            Binary_node.type = BINARY_DATA
            Binary_node.Data = BinaryNode(str(Binary_count))
            Binary_node.Data.Data = whole_data[:Fd_Struct[0][1]]
            Binary_node.Data.Size = len(Binary_node.Data.Data)
            Binary_node.Data.HOffset = 0 + offset
            self.WholeFvTree.insertChild(Binary_node)
            Binary_count += 1
        # Add the first collected Fv image into the tree.
        Cur_node = NODETREE(Fd_Struct[0][0]+ str(Fv_count))
        Cur_node.type = Fd_Struct[0][0]
        Cur_node.Data = FvNode(Fv_count, whole_data[Fd_Struct[0][1]:Fd_Struct[0][1]+Fd_Struct[0][2][0]])
        Cur_node.Data.HOffset = Fd_Struct[0][1] + offset
        Cur_node.Data.DOffset = Cur_node.Data.HOffset+Cur_node.Data.Header.HeaderLength
        Cur_node.Data.Data = whole_data[Fd_Struct[0][1]+Cur_node.Data.Header.HeaderLength:Fd_Struct[0][1]+Cur_node.Data.Size]
        self.WholeFvTree.insertChild(Cur_node)
        Fv_count += 1
        Fv_num = len(Fd_Struct)
        # Add all the collected Fv image and the Binary Fv image between them into the tree.
        for i in range(Fv_num-1):
            if Fd_Struct[i][1]+Fd_Struct[i][2][0] != Fd_Struct[i+1][1]:
                Binary_node = NODETREE('BINARY'+ str(Binary_count))
                Binary_node.type = BINARY_DATA
                Binary_node.Data = BinaryNode(str(Binary_count))
                Binary_node.Data.Data = whole_data[Fd_Struct[i][1]+Fd_Struct[i][2][0]:Fd_Struct[i+1][1]]
                Binary_node.Data.Size = len(Binary_node.Data.Data)
                Binary_node.Data.HOffset = Fd_Struct[i][1]+Fd_Struct[i][2][0] + offset
                self.WholeFvTree.insertChild(Binary_node)
                Binary_count += 1
            Cur_node = NODETREE(Fd_Struct[i+1][0]+ str(Fv_count))
            Cur_node.type = Fd_Struct[i+1][0]
            Cur_node.Data = FvNode(Fv_count, whole_data[Fd_Struct[i+1][1]:Fd_Struct[i+1][1]+Fd_Struct[i+1][2][0]])
            Cur_node.Data.HOffset = Fd_Struct[i+1][1] + offset
            Cur_node.Data.DOffset = Cur_node.Data.HOffset+Cur_node.Data.Header.HeaderLength
            Cur_node.Data.Data = whole_data[Fd_Struct[i+1][1]+Cur_node.Data.Header.HeaderLength:Fd_Struct[i+1][1]+Cur_node.Data.Size]
            self.WholeFvTree.insertChild(Cur_node)
            Fv_count += 1
        # If the final Fv image is the Binary Fv, add it into the tree
        if Fd_Struct[-1][1] + Fd_Struct[-1][2][0] != data_size:
            Binary_node = NODETREE('BINARY'+ str(Binary_count))
            Binary_node.type = BINARY_DATA
            Binary_node.Data = BinaryNode(str(Binary_count))
            Binary_node.Data.Data = whole_data[Fd_Struct[-1][1]+Fd_Struct[-1][2][0]:]
            Binary_node.Data.Size = len(Binary_node.Data.Data)
            Binary_node.Data.HOffset = Fd_Struct[-1][1]+Fd_Struct[-1][2][0] + offset
            self.WholeFvTree.insertChild(Binary_node)
        print('Final:', [x.key for x in self.WholeFvTree.Child])

    ## Parser the nodes in WholeTree.
    def ParserFromRoot(self, WholeFvTree=None, whole_data=b'', Reloffset = 0):
        # If the current node is the root, it is the start of this parser.
        if WholeFvTree.type == ROOT_TREE or WholeFvTree.type == ROOT_FV_TREE:
            self.ParserData(whole_data, Reloffset)
            print("\nParser Fd Start!\n")
        # If the current node is a FvNode, parse it to create the Ffs node and get the Ffs info.
        elif WholeFvTree.type == FV_TREE or WholeFvTree.type == SEC_FV_TREE or WholeFvTree.type == ROOT_FFS_TREE:
            print('\nThis is the Fv leaf!')
            self.ParserFv(WholeFvTree, whole_data, Reloffset)
        # If the current node is a SectionNode, parse it to get the section info and do it in circle.
        elif WholeFvTree.type == FFS_TREE or WholeFvTree.type == ROOT_SECTION_TREE:
            print('This is the Ffs leaf!\n')
            self.ParserFfs(WholeFvTree, whole_data, Reloffset)
        # If the current node is a FfsNode with data, skip it as it is only used to save data.
        elif WholeFvTree.type == SECTION_TREE:
            print('This is the Section leaf/Encapsulation!\n')
            self.ParserSection(WholeFvTree)
        # If the current node is a BinaryNode/FFsPad/FFsFreeSpace/DataFvNode, skip it as it is only used to save data.
        elif WholeFvTree.type == BINARY_DATA or WholeFvTree.type == FFS_PAD or WholeFvTree.type == FFS_FREE_SPACE or WholeFvTree.type == DATA_FV_TREE:
            print("{} data!".format(WholeFvTree.type))
            print("Skip parser {}!\n".format(WholeFvTree.key))
        # If the current node is not in the types above, print error info.
        else:
            print(WholeFvTree.type)
            print("\nWrong node type!\n")
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

def SaveTreeInfo(TreeInfo, outputname):
    with open(outputname, "w") as f:
        for item in TreeInfo:
            f.writelines(item + '\n')

# The ROOT_TYPE can be 'ROOT_TREE', 'ROOT_FV_TREE', 'ROOT_FFS_TREE', 'ROOT_SECTION_TREE'
def ParserFile(inputfile, outputfile, ROOT_TYPE):
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TYPE)
    print("\nParserData Start!\n")
    # FmmtParser.WholeFvTree.Data = whole_data
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Parser_{}.log".format(os.path.basename(inputfile)))
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

def DeleteFv(inputfile, TargetFv_name, outputfile):
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    FmmtParser.WholeFvTree.FindNode(TargetFv_name, FmmtParser.WholeFvTree.Findlist)
    print(FmmtParser.WholeFvTree.Findlist)
    if FmmtParser.WholeFvTree.Findlist != []:
        for item in FmmtParser.WholeFvTree.Findlist:
            print('DeleteTree.key', item)
            print('DeleteTree.ParTree', item.Parent.key)
            item.type = BINARY_DATA
            item.Data.Data = b'\xff' * item.Data.Size
            FmmtParser.ReCompressed(item.Parent)
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Delete_{}.log".format(os.path.basename(inputfile)))
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

def DeleteFfs(inputfile, TargetFfs_name, outputfile, Fv_name=None):
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)

    FmmtParser.WholeFvTree.FindNode(TargetFfs_name, FmmtParser.WholeFvTree.Findlist)
    print(FmmtParser.WholeFvTree.Findlist)
    # Choose the Specfic DeleteFfs with Fv info
    if Fv_name:
        for item in FmmtParser.WholeFvTree.Findlist:
            if item.Parent.key != Fv_name and item.Parent.Data.Name != Fv_name:
                FmmtParser.WholeFvTree.Findlist.remove(item)
    print(FmmtParser.WholeFvTree.Findlist)
    print(FmmtParser.WholeFvTree.Findlist[0].Data.Name)
    if FmmtParser.WholeFvTree.Findlist != []:
        for Delete_Ffs in FmmtParser.WholeFvTree.Findlist:
            Delete_Fv = Delete_Ffs.Parent
            LastFfs = Delete_Ffs.LastRel
            NextFfs = Delete_Ffs.NextRel
            if LastFfs and LastFfs.type == FFS_PAD:
                # Both LastNode and NextNode are FFS_PAD
                if NextFfs and NextFfs.type == FFS_PAD:
                    AppendBytes = b'\xff' * ((Delete_Ffs.Data.Header.HeaderLength*2) + \
                                    len(Delete_Ffs.Data.Data)) + Delete_Ffs.Data.PadData + \
                                    NextFfs.Data.Data + NextFfs.Data.PadData
                    AppendSize = len(AppendBytes)
                    LastFfs.Data.Size += AppendSize
                    FmmtParser.ChangeSize(LastFfs, -AppendSize)
                    LastFfs.Data.Data += AppendBytes
                    LastFfs.NextRel = NextFfs.NextRel
                    NextFfs.NextRel.LastRel = LastFfs
                    Delete_Fv.Child.remove(Delete_Ffs)
                    Delete_Fv.Child.remove(NextFfs)
                # Both LastNode and NextNode are FFS_PAD, and NextNode is the last node
                elif NextFfs and NextFfs.type == FFS_FREE_SPACE:
                    LastFfs.type == FFS_FREE_SPACE
                    LastFfs.Data.Data = b'\xff'*(LastFfs.Data.Header.HeaderLength + \
                                        len(LastFfs.Data.Data) + \
                                        Delete_Ffs.Data.Header.HeaderLength + \
                                        len(Delete_Ffs.Data.Data) + \
                                        len(NextFfs.Data.Data))
                    LastFfs.NextRel = None
                    Delete_Fv.Child.remove(Delete_Ffs)
                    Delete_Fv.Child.remove(NextFfs)
                # Only LastNode is FFS_PAD
                elif NextFfs:
                    AppendBytes = b'\xff' * (Delete_Ffs.Data.Header.HeaderLength + \
                                    len(Delete_Ffs.Data.Data)) + Delete_Ffs.Data.PadData
                    AppendSize = len(AppendBytes)
                    LastFfs.Data.Size += AppendSize
                    FmmtParser.ChangeSize(LastFfs, -AppendSize)
                    LastFfs.Data.Data += AppendBytes
                    LastFfs.NextRel = Delete_Ffs.NextRel
                    Delete_Ffs.NextRel.LastRel = LastFfs
                    Delete_Fv.Child.remove(Delete_Ffs)
                # The Target FFs is the last node
                else:
                    LastFfs.type == FFS_FREE_SPACE
                    LastFfs.Data.Data = b'\xff'*(LastFfs.Data.Header.HeaderLength + \
                                        len(LastFfs.Data.Data) + \
                                        len(Delete_Ffs.Data.Data))
                    LastFfs.NextRel = None
                    Delete_Fv.Child.remove(Delete_Ffs)
            # if LastFfs is not the FFS_PAD
            elif LastFfs:
                # if the NextFfs is a FFS_PAD, combine
                if NextFfs and NextFfs.type == FFS_PAD:
                    AppendBytes = b'\xff' * NextFfs.Data.Header.HeaderLength + \
                                    NextFfs.Data.Data + NextFfs.Data.PadData
                    AppendSize = len(AppendBytes)
                    Delete_Ffs.Data.Size += AppendSize
                    Delete_Ffs.type = FFS_PAD
                    Delete_Ffs.Data.Name = PADVECTOR
                    FmmtParser.ChangeSize(Delete_Ffs, -AppendSize)
                    Delete_Ffs.Data.Data = b'\xff' * len(Delete_Ffs.Data.Data) + AppendBytes
                    Delete_Ffs.NextRel = NextFfs.NextRel
                    NextFfs.NextRel.LastRel = Delete_Ffs
                    Delete_Fv.Child.remove(NextFfs)
                # if the NextFfs is a FFS_PAD, and it is the last node.
                elif NextFfs and NextFfs.type == FFS_FREE_SPACE:
                    Delete_Ffs.type == FFS_FREE_SPACE
                    Delete_Ffs.Data.Data = b'\xff'*(Delete_Ffs.Data.Header.HeaderLength + \
                                        len(Delete_Ffs.Data.Data) + \
                                        len(NextFfs.Data.Data))
                    Delete_Ffs.NextRel = None
                    Delete_Fv.Child.remove(NextFfs)
                # if the NextFfs is a common Ffs
                elif NextFfs:
                        Delete_Ffs.type == FFS_PAD
                        Delete_Ffs.Data.Name = PADVECTOR
                        Delete_Ffs.Data.Data = b'\xff'*(len(Delete_Ffs.Data.Data))
                # if the target FFs is the last node
                else:
                    Delete_Ffs.type == FFS_FREE_SPACE
                    Delete_Ffs.Data.Data = b'\xff'* (Delete_Ffs.Data.Header.HeaderLength + \
                                        len(Delete_Ffs.Data.Data))
            # if Last node not exist, the target ffs is the first ffs
            else:
                # if Next ffs is a common ffs
                if NextFfs and NextFfs.type != FFS_PAD and NextFfs.type != FFS_FREE_SPACE:
                    Delete_Ffs.type == FFS_PAD
                    Delete_Ffs.Data.Name = PADVECTOR
                    Delete_Ffs.Data.Data = b'\xff'*(len(Delete_Ffs.Data.Data))
                elif NextFfs and NextFfs.type == FFS_PAD:
                    AppendBytes = b'\xff' * NextFfs.Data.Header.HeaderLength + \
                                    NextFfs.Data.Data + NextFfs.Data.PadData
                    AppendSize = len(AppendBytes)
                    Delete_Ffs.Data.Size += AppendSize
                    Delete_Ffs.type = FFS_PAD
                    Delete_Ffs.Data.Name = PADVECTOR
                    FmmtParser.ChangeSize(Delete_Ffs, -AppendSize)
                    Delete_Ffs.Data.Data = b'\xff' * len(Delete_Ffs.Data.Data) + AppendBytes
                    Delete_Ffs.NextRel = NextFfs.NextRel
                    NextFfs.NextRel.LastRel = Delete_Ffs
                    Delete_Fv.Child.remove(NextFfs)
                # if the Fv only have the target ffs with content       
                else:
                    if NextFfs:
                        Delete_Ffs.type = FFS_PAD
                        Delete_Ffs.Data.Name = PADVECTOR
                        Delete_Ffs.Data.Data = b'\xff' * len(Delete_Ffs.Data.Data)
                    else:
                        Delete_Ffs.type = FFS_FREE_SPACE
                        Delete_Ffs.Data.Data = b'\xff' * (NextFfs.Data.Header.HeaderLength + len(Delete_Ffs.Data.Data))
        FmmtParser.ReCompressed(Delete_Fv)
        FmmtParser.BinaryInfo = []
        FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
        SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Delete_{}.log".format(os.path.basename(inputfile)))
        FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
        with open(outputfile, "wb") as f:
            f.write(FmmtParser.FinalData)

def AddNewFfs(inputfile, Fv_name, newffsfile, outputfile):
    # Create input file WholeTree
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    # Get Target Fv and Target Ffs_Pad
    FmmtParser.WholeFvTree.FindNode(Fv_name, FmmtParser.WholeFvTree.Findlist)
    # Create new ffs Tree
    with open(newffsfile, "rb") as f:
        new_ffs_data = f.read()
    NewFmmtParser = FMMTParser(newffsfile, FV_TREE)
    FindSpace = False
    for TargetFv in FmmtParser.WholeFvTree.Findlist:
        if TargetFv.Child[-1].type == FFS_FREE_SPACE:
            TargetFfsPad = TargetFv.Child[-1]
            Target_index = -1
            FindSpace = True
            print(TargetFfsPad.key)
        if FindSpace:
            Pad_len = TargetFfsPad.Data.Header.HeaderLength + len(TargetFfsPad.Data.Data) + len(TargetFfsPad.Data.PadData)
            print('Pad_len', Pad_len)
            new_ffs_len = len(new_ffs_data)
            print('new_ffs_len', new_ffs_len)
            if new_ffs_len > Pad_len:
                print('The new Ffs is too large !!! Could not add it into the Target Fv !')
            else:
                delta_data = b'\xff' * (Pad_len - new_ffs_len)
                new_ffs_data += delta_data
                print("NewFFsData Parser!!!!!!!!!!!")
                print("Data offset Test:", TargetFfsPad.Data.HOffset)
                NewFmmtParser.ParserFromRoot(NewFmmtParser.WholeFvTree, new_ffs_data, TargetFfsPad.Data.HOffset)
                print('NewFmmtParser.WholeFvTree.Child', NewFmmtParser.WholeFvTree.Child)
                print('TargetFv_ori', TargetFv.Child)
                TargetFv.Child.remove(TargetFfsPad)
                print('TargetFv_del', TargetFv.Child)
                for item in NewFmmtParser.WholeFvTree.Child:
                    TargetFv.insertChild(item, Target_index)
                    Target_index += 1
                FmmtParser.ReCompressed(TargetFv)
        else:
            print("TargetFv does not have enough space for adding!")
            break
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Add_.log".format(os.path.basename(inputfile)))
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

## Not works
def ReplaceFfs(inputfile, Ffs_name, newffsfile, outputfile):
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    with open(newffsfile, "rb") as f:
        new_ffs_data = f.read()
    newFmmtParser = FMMTParser(newffsfile, FV_TREE)
    newFmmtParser.ParserFromRoot(newFmmtParser.WholeFvTree, new_ffs_data)
    new_ffs = newFmmtParser.WholeFvTree.Child[0]
    new_ffs.Data.PadData = newFmmtParser.GetPadSize(new_ffs.Data.Size, 8) * b'\xff'
    FmmtParser.WholeFvTree.FindNode(Ffs_name, FmmtParser.WholeFvTree.Findlist)
    if FmmtParser.WholeFvTree.Findlist != []:
        for TargetFfs in FmmtParser.WholeFvTree.Findlist:
            NextFfs = TargetFfs.NextRel
            if NextFfs and NextFfs.type == FFS_FREE_SPACE:
                if len(new_ffs.Data.Data) > len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) + len(NextFfs.Data.Data):
                    print('The new ffs is too large, could not replace!!')
                    break
                # new_ffs is smaller than origin ffs
                elif len(new_ffs.Data.Data) < len(TargetFfs.Data.Data):
                    offset_delta = len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - len(new_ffs.Data.Data) - len(new_ffs.Data.PadData)
                    NextFfs.Data.Data += b'\xff'*(offset_delta)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.ReCompressed(TargetParent)
                elif len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) >= len(new_ffs.Data.Data) >= len(TargetFfs.Data.Data):
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.ReCompressed(TargetParent)
                else:
                    offset_delta = len(new_ffs.Data.Data) + len(new_ffs.Data.PadData) - len(TargetFfs.Data.Data) - len(TargetFfs.Data.PadData)
                    NextFfs.Data.Data = b'\xff' * (len(NextFfs.Data.Data) - offset_delta)
                    NextFfs.Data.HOffset += offset_delta
                    NextFfs.Data.DOffset += offset_delta
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.ReCompressed(TargetParent)
            elif NextFfs and NextFfs.type == FFS_PAD:
                if len(new_ffs.Data.Data) > len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) + len(NextFfs.Data.Data) + len(NextFfs.Data.PadData):
                    print('The new ffs is too large, could not replace!!')
                    break
                elif len(new_ffs.Data.Data) < len(TargetFfs.Data.Data):
                    offset_delta = len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - len(new_ffs.Data.Data) - len(new_ffs.Data.PadData)
                    NextFfs.Data.Data += b'\xff' * (offset_delta)
                    NextFfs.Data.HOffset -= offset_delta
                    NextFfs.Data.DOffset -= offset_delta
                    NextFfs.Data.Size += offset_delta
                    FmmtParser.ChangeSize(NextFfs, -offset_delta)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.ReCompressed(TargetParent)
                elif len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) >= len(new_ffs.Data.Data) >= len(TargetFfs.Data.Data):
                    print(newFmmtParser.WholeFvTree.Child[0].key)
                    print('TargetFfs.Pad', TargetFfs.Data.PadData)
                    print('new_ffs.Pad', new_ffs.Data.PadData)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.ReCompressed(TargetParent)
                else:
                    offset_delta = len(new_ffs.Data.Data) + len(new_ffs.Data.PadData) - len(TargetFfs.Data.Data) - len(TargetFfs.Data.PadData)
                    NextFfs.Data.Data = b'\xff' * (len(NextFfs.Data.Data) - offset_delta)
                    NextFfs.Data.HOffset += offset_delta
                    NextFfs.Data.DOffset += offset_delta
                    NextFfs.Data.Size -= offset_delta
                    FmmtParser.ChangeSize(NextFfs, offset_delta)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.ReCompressed(TargetParent)
            else:
                if len(new_ffs.Data.Data) > len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData):
                    print('The new ffs is too large, could not replace!!')
                    break
                elif len(new_ffs.Data.Data) > len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - TargetFfs.Data.Header.HeaderLength:
                    offset_delta = len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - len(new_ffs.Data.Data)
                    new_ffs.Data.Data += b'\xff' * (offset_delta)
                    new_ffs.Data.PadData = b''
                    new_ffs.Data.Size += offset_delta
                    FmmtParser.ChangeSize(NextFfs, -offset_delta)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.ReCompressed(TargetParent)
                else:
                    offset_delta = len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - len(new_ffs.Data.Data)
                    new_ffs_pad = NODETREE(PADVECTOR)
                    new_ffs_pad.type = FFS_PAD
                    new_ffs_pad.Data = FfsNode(b'\xff'* offset_delta)
                    new_ffs_pad.Data.Size = offset_delta
                    FmmtParser.ChangeSize(NextFfs)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    TargetParent.insertChild(new_ffs_pad, Target_index+1)
                    FmmtParser.ReCompressed(TargetParent)
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Replace_{}.log".format(os.path.basename(inputfile)))
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

def ExtractFfs(inputfile, Ffs_name, outputfile):
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    FmmtParser.WholeFvTree.FindNode(Ffs_name, FmmtParser.WholeFvTree.Findlist)
    if FmmtParser.WholeFvTree.Findlist != []:
        TargetNode = FmmtParser.WholeFvTree.Findlist[0]
        print(type(TargetNode.Data.Header.Size[0]))
        print(hex(TargetNode.Data.Header.Size[0]))
        print(hex(TargetNode.Data.Header.Size[1]))
        print(hex(TargetNode.Data.Header.Size[2]))
        FinalData = struct2stream(TargetNode.Data.Header) + TargetNode.Data.Data
        with open(outputfile, "wb") as f:
            f.write(FinalData)
    else:
        print('Could not find the target ffs!')

def Usage():
    pass

def main():
    Usage()
    inputfile = "Input\OVMF.fd"
    # inputfile = "Input\Platform_SPR_EBG_TXTSX_Setup.fd"
    # inputfile = "Input\Storage.ffs"
    # inputfile = "Output\Output_E.ffs"
    # inputfile = "Output\Output.fd"
    # inputfile = "Input\PEIFV.Fv"
    # inputfile = "Input\SECFV.Fv"
    # inputfile = "Input\OVMF_VARS.fd"
    # inputfile = "Input\OVMF_CODE.fd"
    # inputfile = "Output\Output_D.fd"
    # NewFvfile = "Input\PEIFV.Fv"
    # NewFfsfile = "Output\Extract.ffs"
    # ParserFile(inputfile, r'Output\Parser.fd', ROOT_TREE)
    # ParserFile(r'Output\Output_DFfs.fd', r'Output\Parser_test.fd', ROOT_TREE)
    # ParserFile(inputfile, r'Output\Storage_test.ffs', ROOT_FFS_TREE)
    # ExtractFfs(inputfile, uuid.UUID("003e7b41-98a2-4be2-b27a-6c30c7655225"), 'Output\E_Test.ffs')
    # ExtractFfs(inputfile, uuid.UUID("a0c98b77-cba5-4bb8-993b-4af6ce33ece4"), 'Output\Extract_c.ffs')
    # ExtractFfs(inputfile, uuid.UUID("df1ccef6-f301-4a63-9661-fc6030dcc880"), 'Output\Extract.ffs')
    # DeleteFfs(inputfile, uuid.UUID("df1ccef6-f301-4a63-9661-fc6030dcc880"), 'Output\Output_DFfs.fd', uuid.UUID('763bed0d-de9f-48f5-81f1-3e90e1b1a015'))
    # DeleteFfs(inputfile, uuid.UUID("9b3ada4f-ae56-4c24-8dea-f03b7558ae50"), 'Output\Output_DFfs.fd')
    
    # AddNewFfs('Output\Output_DFfs.fd', 'FV2', NewFfsfile, 'Output\Output_Affs.fd')
    # DeleteFv(inputfile, '763bed0d-de9f-48f5-81f1-3e90e1b1a015', 'Output\Output_D.fd')
    # DeleteFv(inputfile, 'FV2', 'Output\Output_D.fd')
    # AddNewFv(inputfile, NewFvfile, 'Output\Output_Afv.fd)
    ReplaceFfs(inputfile, uuid.UUID("df1ccef6-f301-4a63-9661-fc6030dcc880"), 'Output\Extract_c.ffs', 'Output\Replace.fd')
    # ReplaceFfs('Output\Replace.fd', uuid.UUID("a0c98b77-cba5-4bb8-993b-4af6ce33ece4"), 'Output\Extract.ffs', 'Output\Replace_back.fd')

if __name__ == '__main__':
    main()