## @file
# This file is used to parser the image as a tree.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent

##
from PI.FvHeader import *
from PI.FfsFileHeader import *
from PI.SectionHeader import *
from core.GuidTools import *
import uuid
import copy

EFI_FIRMWARE_FILE_SYSTEM2_GUID = uuid.UUID("8c8ce578-8a3d-4f1c-9935-896185c32dd3")
EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE = EFI_FIRMWARE_FILE_SYSTEM2_GUID.bytes
EFI_FIRMWARE_FILE_SYSTEM3_GUID = uuid.UUID("5473C07A-3DCB-4dca-BD6F-1E9689E7349A")
EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE = b'x\xe5\x8c\x8c=\x8a\x1cO\x995\x89a\x85\xc3-\xd3'
EFI_SYSTEM_NVDATA_FV_GUID = uuid.UUID("fff12b8d-7696-4c8b-a985-2747075b4f50")
EFI_SYSTEM_NVDATA_FV_GUID_BYTE = b"\x8d+\xf1\xff\x96v\x8bL\xa9\x85'G\x07[OP"
ZEROVECTOR = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
PADVECTOR = uuid.UUID("ffffffff-ffff-ffff-ffff-ffffffffffff")
FVH_SIGNATURE = b'_FVH'

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
FV_TREE = 'FV'
DATA_FV_TREE = 'DATA_FV'
FFS_TREE = 'FFS'
FFS_PAD = 'FFS_PAD'
SECTION_TREE = 'SECTION'
SEC_FV_TREE = 'SEC_FV_IMAGE'
BINARY_DATA = 'BINARY'

HeaderType = {0x01:EFI_COMPRESSION_SECTION, 
            0x02:EFI_GUID_DEFINED_SECTION, 
            0x14:EFI_SECTION_VERSION,
            0x15:EFI_SECTION_USER_INTERFACE,
            0x18:EFI_FREEFORM_SUBTYPE_GUID_SECTION,
        }

# Section_Count = 0
Fv_count = 0
TreeInfo = []

class BinaryNode:
    def __init__(self, name):
        self.Size = 0
        self.Name = "BINARY" + str(name)
        self.HOffset = 0
        self.Data = b''

class FvNode:
    def __init__(self, name, buffer: bytes):
        self.Header = EFI_FIRMWARE_VOLUME_HEADER(buffer)
        self.Name = "FV" + str(name)
        if self.Header.ExtHeader:
            self.Name = self.Header.ExtHeader.FvName_uuid
        self.Size = self.Header.FvLength
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        if self.Header.Signature != b'_FVH':
            print('Error Fv Header!!')
        self.PadData = b''

class FfsNode:
    def __init__(self, buffer: bytes):
        self.Attributes = unpack("<B", buffer[19:20])[0]
        if self.Attributes != 0x01:
            self.Header = EFI_FFS_FILE_HEADER(buffer)
        else:
            self.Header = EFI_FFS_FILE_HEADER2(buffer)
        self.Name = self.Header.Name_uuid
        self.Size = self.Header.FFS_FILE_SIZE
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        self.PadData = b''

class SectionNode:
    def __init__(self, buffer: bytes):
        if buffer[4:7] != b'\xff\xff\xff':
            self.Header = EFI_COMMON_SECTION_HEADER(buffer)
        else:
            self.Header = EFI_COMMON_SECTION_HEADER2(buffer)
        if self.Header.Type in SectionHeaderType:
            self.Name = SectionHeaderType[self.Header.Type]
        else:
            self.Name = "SECTION"
        if self.Header.Type in HeaderType:
            self.ExtHeader = self.GetExtHeader(self.Header.Type, buffer[self.Header.common_head_size:])
            self.HeaderLength = self.Header.common_head_size + self.ExtHeader.ExtHeaderSize()
        else:
            self.ExtHeader = None
            self.HeaderLength = self.Header.common_head_size
        self.Size = self.Header.SECTION_SIZE
        self.Type = self.Header.Type
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        self.OriData = b''
        self.OriHeader = b''
        self.PadData = b''

    def GetExtHeader(self, Type, buffer):
        if Type == 0x01:
            return EFI_COMPRESSION_SECTION(buffer)
        elif Type == 0x02:
            return EFI_GUID_DEFINED_SECTION(buffer)
        elif Type == 0x14:
            return EFI_SECTION_VERSION(buffer)
        elif Type == 0x15:
            return EFI_SECTION_USER_INTERFACE(buffer)
        elif Type == 0x18:
            return EFI_FREEFORM_SUBTYPE_GUID_SECTION(buffer)

class NODETREE:
    def __init__(self, NodeName):
        self.key = NodeName
        self.type = None
        self.Data = None
        self.Child = []
        self.OriChild = []
        self.Parent = None
        self.NextRel = None
        self.LastRel = None
 
    # FvTree.insertChild()
    def insertChild(self, newNode):
        if len(self.Child) == 0:
            self.Child.append(newNode)
            newNode.Parent = self
        else:
            LastTree = self.Child[-1]
            self.Child.append(newNode)
            LastTree.NextRel = newNode
            newNode.LastRel = LastTree
            newNode.Parent = self

    # insertRel(lastNode, newNode)
    def insertRel(self, lastNode, newNode):
        parentTree = lastNode.getParent()
        parentTree.Child.append(newNode)
        lastNode.NextRel = newNode
        newNode.LastRel = lastNode

    def deleteNode(self, root, deletekey):
        deleteTree = self.FindNode(root, deletekey)
        parentTree = deleteTree.getParent()
        lastTree = deleteTree.getLastRel()
        nextTree = deleteTree.getNextRel()
        if parentTree:
            parentTree.Child.remove(deleteTree)
        if lastTree and nextTree:
            lastTree.NextRel = nextTree
            nextTree.LastRel = lastTree
        elif lastTree:
            lastTree.NextRel = None
        else:
            nextTree.LastRel = None

    def getParent(self):
        return self.Parent

    def parserTree(self, TreeInfo, space =""):
        if self.type == ROOT_TREE:
            print("Name:{}  Type:{}  FilesNum:{}".format(self.key, self.type, len(self.Child)))
            TreeInfo.append("Name:{}  Type:{}  FilesNum:{}".format(self.key, self.type, len(self.Child)))
        elif self is not None:
            print("{}Name:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.key, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
            TreeInfo.append("{}Name:{}  Type:{}  Size:{}  Offset:{}  FilesNum:{}".format(space, self.key, self.type, hex(self.Data.Size), hex(self.Data.HOffset), len(self.Child)))
        space += "  "
        for item in self.Child:
            item.parserTree(TreeInfo, space)

    def isFinalChild(self):
        ParTree = self.getParent()
        if ParTree:
            if ParTree.Child[-1] == self:
                return True
        return False

    def FindNode(self, key):
        print(self.key, key)
        if self.key == key:
            print("root, ", self)
            return self
        for item in self.Child:
            return item.FindNode(key)

class FMMTParser:
    def __init__(self, name, TYPE):
        self.WholeFvTree = NODETREE(name)
        self.WholeFvTree.type = TYPE
        self.FinalData = b''
        self.BinaryInfo = []

    ## Use GuidTool to decompress data.
    def DeCompressData(self, GuidTool, Section_Data):
        print('len_Section_Data', len(Section_Data))
        guidtool = GUIDTools(r'C:\Users\yuweiche\Code\FMMT2\FMMTConfig.ini').__getitem__(GuidTool)
        print(guidtool)
        print(guidtool.command)
        DecompressedData = guidtool.unpack(Section_Data)
        return DecompressedData

    ## Decompress the compressed section.
    def ParserSection(self, Section_Tree):
        print("Start DeCompressSection")
        print(Section_Tree.Data.Type)
        if Section_Tree.Data.Type == 0x01:
            Section_Tree.Data.OriData = Section_Tree.Data.Data
            # Section_Tree.Data.Data = self.Decompress(Section_Tree.Data.Data)
            self.ParserFfs(Section_Tree, b'')
        elif Section_Tree.Data.Type == 0x02:
            print("GuidTool*************************************************")
            Section_Tree.Data.OriData = Section_Tree.Data.Data
            DeCompressGuidTool = Section_Tree.Data.ExtHeader.SectionDefinitionGuid_uuid
            Section_Tree.Data.Data = self.DeCompressData(DeCompressGuidTool, Section_Tree.Data.Data)
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
            Sec_Fv_Tree = NODETREE(Fv_count)
            Sec_Fv_Tree.type = SEC_FV_TREE
            Sec_Fv_Tree.Data = Sec_Fv_Info
            Sec_Fv_Tree.Data.HOffset = Section_Tree.Data.DOffset
            Sec_Fv_Tree.Data.DOffset = Sec_Fv_Tree.Data.HOffset + Sec_Fv_Tree.Data.Header.HeaderLength
            Sec_Fv_Tree.Data.Data = Section_Tree.Data.Data[Sec_Fv_Tree.Data.Header.HeaderLength:]
            Section_Tree.insertChild(Sec_Fv_Tree)

    # ParserFFs / GetSection
    def ParserFfs(self, ParTree=None, Whole_Data=b''):
        print('\nParserFfs Start!')
        print('{} - Section '.format(ParTree.key))
        # Section_Count = 0
        Rel_Offset = 0
        Section_Offset = 0
        if ParTree:
            Data_Size = len(ParTree.Data.Data)
            Section_Offset = ParTree.Data.DOffset
            Whole_Data = ParTree.Data.Data
        else:
            Data_Size = len(Whole_Data)
        print('  Ffs Data_Size', Data_Size)
        print('  Ffs Data Offset', Section_Offset)
        print('  Ffs Header Offset', ParTree.Data.HOffset)
        while Rel_Offset < Data_Size:
            print('  Rel_Offset', Rel_Offset)
            Section_Info = SectionNode(Whole_Data[Rel_Offset:])
            # Section_Info = SectionNode(Section_Count, Whole_Data[Rel_Offset:])
            Section_Tree = NODETREE(Section_Info.Name)
            print('      GetSection: ', Section_Info.Name)
            Section_Tree.type = SECTION_TREE
            Section_Tree.Data = Section_Info
            Section_Data = Whole_Data[Rel_Offset+Section_Tree.Data.HeaderLength: Rel_Offset+Section_Tree.Data.Size]
            Section_Tree.Data.DOffset = Section_Offset + Section_Tree.Data.HeaderLength
            print('      Section RelDataRange:', Rel_Offset+Section_Tree.Data.HeaderLength, Rel_Offset+Section_Tree.Data.Size)
            print('      Section DataRange:', Section_Offset+Section_Tree.Data.HeaderLength, Section_Offset+Section_Tree.Data.Size)
            print('      Section_Tree.Data.Header.Type', Section_Tree.Data.Header.Type)
            print('      Section_Tree.Data.Header.common_head_size', Section_Tree.Data.Header.common_head_size)
            
            Section_Tree.Data.HOffset = Section_Offset
            Section_Tree.Data.ROffset = Rel_Offset
            Section_Tree.Data.Data = Section_Data
            print('      Section_Tree.Data.Data length', len(Section_Tree.Data.Data))
            print('      Section_Tree.Data.Size', Section_Tree.Data.Size)

            Pad_Size = 0
            if (Rel_Offset+Section_Tree.Data.HeaderLength+len(Section_Tree.Data.Data) != Data_Size) and Section_Tree.Data.Size % 4 != 0:
                Pad_Size = 4 - Section_Tree.Data.Size % 4
                Section_Tree.Data.PadData = Pad_Size * b'\x00'
                print('      Add PadDataSize: ', Pad_Size)
            
            print("**************************OriType", Section_Tree.Data.Header.Type)
            if Section_Tree.Data.Header.Type == 0x02:
                Section_Tree.Data.DOffset = Section_Offset + Section_Tree.Data.ExtHeader.DataOffset
                Section_Tree.Data.Data = Whole_Data[Rel_Offset+Section_Tree.Data.ExtHeader.DataOffset: Rel_Offset+Section_Tree.Data.Size]
                print('      Section_Tree.Data.DOffset', Section_Tree.Data.DOffset)
                print('      Section_Tree.Data.ExtHeader.DataOffset', Section_Tree.Data.ExtHeader.DataOffset)

            Section_Offset += Section_Tree.Data.Size + Pad_Size
            Rel_Offset += Section_Tree.Data.Size + Pad_Size
            # if Section_Tree.Data.HeaderLength + len(Section_Tree.Data.Data) != Data_Size:
            ParTree.insertChild(Section_Tree)

    ##  ParserFv / GetFfs
    def ParserFv(self, ParTree=None, Whole_Data=b''):
        print('\nParserFv Start!')
        print('{} - Ffs '.format(ParTree.key))
        Ffs_Offset = 0
        Rel_Offset = 0
        # Get the Data from parent tree, if do not have the tree then get it from the whole_data.
        if ParTree:
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
            Ffs_Tree.Data.HOffset = Ffs_Offset
            Ffs_Tree.Data.DOffset = Ffs_Offset + Ffs_Tree.Data.Header.HeaderLength
            Ffs_Tree.Data.ROffset = Rel_Offset
            if Ffs_Info.Name == PADVECTOR:
                Ffs_Tree.type = FFS_PAD
                Ffs_Tree.Data.Data = Whole_Data[Rel_Offset+Ffs_Tree.Data.Header.HeaderLength: Rel_Offset+Ffs_Tree.Data.Size]
                Ffs_Tree.Data.Size = len(Ffs_Tree.Data.Data) + Ffs_Tree.Data.Header.HeaderLength
            else:
                Ffs_Tree.type = FFS_TREE
                Ffs_Tree.Data.Data = Whole_Data[Rel_Offset+Ffs_Tree.Data.Header.HeaderLength: Rel_Offset+Ffs_Tree.Data.Size]
            # The final Ffs in Fv does not need to add padding, else must be 8-bytes align with Fv start offset
            Pad_Size = 0
            if (Rel_Offset+Ffs_Tree.Data.Header.HeaderLength+len(Ffs_Tree.Data.Data) != Data_Size) and Ffs_Tree.Data.Size % 8 != 0:  
                Pad_Size = 8 - Ffs_Tree.Data.Size % 8
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
    
    ## Parser the nodes in WholeTree.
    def ParserFromRoot(self, WholeFvTree=None, whole_data=b''):
        # If the current node is a FvNode, parse it to create the Ffs node and get the Ffs info.
        if WholeFvTree.type == FV_TREE or WholeFvTree.type == SEC_FV_TREE:
            print('\nThis is the Fv leaf!')
            print('GetFv: ', WholeFvTree.Data.Name)
            print('  GetFvSize: ', WholeFvTree.Data.Size)
            print('  GetFvHOffset: ', WholeFvTree.Data.HOffset)
            print('  GetFvDOffset: ', WholeFvTree.Data.DOffset)
            self.ParserFv(WholeFvTree, whole_data)
        # If the current node is a SectionNode, parse it to get the section info and do it in circle.
        elif WholeFvTree.type == FFS_TREE:
            print('This is the Ffs leaf!\n')
            self.ParserFfs(WholeFvTree, whole_data)
        # If the current node is a DataFvNode, skip it as it is only used to save the variable data.
        elif WholeFvTree.type == DATA_FV_TREE:
            print('This is the Data storage Fv!\n')
        # If the current node is a FfsNode with data, skip it as it is only used to save data.
        elif WholeFvTree.type == SECTION_TREE:
            print('This is the Section leaf/Encapsulation!\n')
            self.ParserSection(WholeFvTree)
        # If the current node is a BinaryNode, skip it as it is only used to save data.
        elif WholeFvTree.type == BINARY_DATA:
            print("Binary data!")
            print("Skip parser {}!\n".format(WholeFvTree.key))
        # If the current node is PadNode, skip it as it is only used to save space.
        elif WholeFvTree.type == FFS_PAD:
            print("\nParser Fd Start!\n")
        # If the current node is the root, it is the start of this parser.
        elif WholeFvTree.type == ROOT_TREE:
            print("\nParser Fd Start!\n")
        # If the current node is not in the types above, print error info.
        else:
            print(WholeFvTree.type)
            print("\nWrong node type!\n")
        for Child in WholeFvTree.Child:
            self.ParserFromRoot(Child, "")

    ## Get the first level Fv from Fd file.
    def GetFvFromFd(self, whole_data=b''):
        Fd_Struct = []
        data_size = len(whole_data)
        cur_index = 0
        # Get all the EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE FV image offset and length.
        while cur_index < data_size:
            if EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE in whole_data[cur_index:]:
                target_index = whole_data[cur_index:].index(EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE) + cur_index
                if whole_data[target_index+24:target_index+28] == FVH_SIGNATURE and whole_data[target_index-16:target_index] == ZEROVECTOR:
                    Fd_Struct.append([FV_TREE, target_index - 16, unpack("Q", whole_data[target_index+16:target_index+24])])
                    cur_index += Fd_Struct[-1][1] + Fd_Struct[-1][2][0]
                else:
                    cur_index = target_index + 1
            else:
                cur_index = data_size
        cur_index = 0
        # Get all the EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE FV image offset and length.
        while cur_index < data_size:
            if EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE in whole_data[cur_index:]:
                target_index = whole_data[cur_index:].index(EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE) + cur_index
                if whole_data[target_index+24:target_index+28] == FVH_SIGNATURE and whole_data[target_index-16:target_index] == ZEROVECTOR:
                    Fd_Struct.append([FV_TREE, target_index - 16, unpack("Q", whole_data[target_index+16:target_index+24])])
                    cur_index += Fd_Struct[-1][1] + Fd_Struct[-1][2][0]
                else:
                    cur_index = target_index + 1
            else:
                cur_index = data_size
        cur_index = 0
        # Get all the EFI_SYSTEM_NVDATA_FV_GUID_BYTE FV image offset and length.
        while cur_index < data_size:
            if EFI_SYSTEM_NVDATA_FV_GUID_BYTE in whole_data[cur_index:]:
                target_index = whole_data[cur_index:].index(EFI_SYSTEM_NVDATA_FV_GUID_BYTE) + cur_index
                if whole_data[target_index+24:target_index+28] == FVH_SIGNATURE and whole_data[target_index-16:target_index] == ZEROVECTOR:
                    Fd_Struct.append([DATA_FV_TREE, target_index - 16, unpack("Q", whole_data[target_index+16:target_index+24])])
                    cur_index += Fd_Struct[-1][1] + Fd_Struct[-1][2][0]
                else:
                    cur_index = target_index + 1
            else:
                cur_index = data_size
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
    def ParserData(self, whole_data=b''):
        # Get all Fv image in Fd with offset and length
        Fd_Struct = self.GetFvFromFd(whole_data)
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
            Binary_node.Data.HOffset = 0
            self.WholeFvTree.insertChild(Binary_node)
            Binary_count += 1
        # Add the first collected Fv image into the tree.
        Cur_node = NODETREE(Fd_Struct[0][0]+ str(Fv_count))
        Cur_node.type = Fd_Struct[0][0]
        Cur_node.Data = FvNode(Fv_count, whole_data[Fd_Struct[0][1]:Fd_Struct[0][2][0]])
        Cur_node.Data.HOffset = Fd_Struct[0][1]
        Cur_node.Data.DOffset = Fd_Struct[0][1]+Cur_node.Data.Header.HeaderLength
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
                Binary_node.Data.HOffset = Fd_Struct[i][1]+Fd_Struct[i][2][0]
                self.WholeFvTree.insertChild(Binary_node)
                Binary_count += 1
            Cur_node = NODETREE(Fd_Struct[i+1][0]+ str(Fv_count))
            Cur_node.type = Fd_Struct[i+1][0]
            Cur_node.Data = FvNode(Fv_count, whole_data[Fd_Struct[i+1][1]:Fd_Struct[i+1][1]+Fd_Struct[i+1][2][0]])
            Cur_node.Data.HOffset = Fd_Struct[i+1][1]
            Cur_node.Data.DOffset = Fd_Struct[i+1][1]+Cur_node.Data.Header.HeaderLength
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
            Binary_node.Data.HOffset = Fd_Struct[-1][1]+Fd_Struct[-1][2][0]
            self.WholeFvTree.insertChild(Binary_node)
        print('Final:', [x.key for x in self.WholeFvTree.Child])
        # All the FvTrees have been added into the root, now parse each of them.
        self.ParserFromRoot(self.WholeFvTree, b'')

    def Encapsulation(self, rootTree):
        if rootTree.type == ROOT_TREE:
            print('Start at Root !!')
        elif rootTree.type == BINARY_DATA:
            self.FinalData += rootTree.Data.Data
        elif rootTree.Child == [] and (rootTree.type == FV_TREE or rootTree.type == FFS_TREE or rootTree.type == DATA_FV_TREE or rootTree.type == FFS_PAD):
            print('Encapsulation leaf Fv/Ffs - {} Data'.format(rootTree.key))
            self.FinalData += rootTree.Data.Header.Encode() + rootTree.Data.Data + rootTree.Data.PadData
            if rootTree.isFinalChild():
                ParTree = rootTree.getParent()
                if ParTree.type != 'ROOT':
                    self.FinalData += ParTree.Data.PadData
        elif rootTree.Child != [] and (rootTree.type == FV_TREE or rootTree.type == FFS_TREE):
            print('Encapsulation Encap Fv/Ffs- {}'.format(rootTree.key))
            self.FinalData += rootTree.Data.Header.Encode()
        elif rootTree.type == SECTION_TREE and rootTree.Data.OriData == b'':
            print('Encapsulation Uncompress Section - {} Data'.format(rootTree.key))
            if rootTree.Data.ExtHeader:
                self.FinalData += rootTree.Data.Header.Encode() + rootTree.Data.ExtHeader.Encode() + rootTree.Data.Data + rootTree.Data.PadData
            else:
                self.FinalData += rootTree.Data.Header.Encode() + rootTree.Data.Data + rootTree.Data.PadData
            rootTree.Child = []
            if rootTree.isFinalChild():
                ParTree = rootTree.getParent()
                self.FinalData += ParTree.Data.PadData
        elif rootTree.type == SECTION_TREE and rootTree.Data.OriData != b'':
            print('Encapsulation Compressed Section- {} Data'.format(rootTree.key))
            if rootTree.Data.ExtHeader:
                self.FinalData += rootTree.Data.Header.Encode() + rootTree.Data.ExtHeader.Encode() + rootTree.Data.OriData + rootTree.Data.PadData
            else:
                self.FinalData += rootTree.Data.Header.Encode() + rootTree.Data.OriData + rootTree.Data.PadData
            rootTree.Child = []
            if rootTree.isFinalChild():
                ParTree = rootTree.getParent()
                self.FinalData += ParTree.Data.PadData
        for Child in rootTree.Child:
            self.Encapsulation(Child)

def SaveTreeInfo(TreeInfo):
    with open("BinaryInfo.log", "w") as f:
        for item in TreeInfo:
            f.writelines(item + '\n')

def ParserFd(inputfile, outputfile):
    with open(inputfile, "rb") as f:
        whole_data = f.read()      
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    print("\nParserData Start!\n")
    FmmtParser.ParserData(whole_data)
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo)
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

def AddNewFv():
    pass
def AddNewFfs():
    pass

def DeleteFv():
    pass

def DeleteFfs():
    pass

def Usage():
    pass

def main():
    Usage()
    inputfile = "OVMF.fd"
    # file = "PEIFV.Fv"
    # file = "OVMF_VARS.fd"
    # file = "OVMF_CODE.fd"
    # file = "MEMFD.fd"
    outputfile = "Output.fd"
    ParserFd(inputfile, outputfile)

if __name__ == '__main__':
    main()