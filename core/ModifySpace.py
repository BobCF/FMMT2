import os
from core.NodeTree import *
from core.GuidTools import GUIDTools
from core.NodeClass import *
from PI.Common import *
from PI.ExtendCType import *

BlockSize = 0x1000
EFI_FVB2_ERASE_POLARITY = 0x00000800

class FfsModify:
    def __init__(self, NewFfs, TargetFfs):
        self.NewFfs = NewFfs
        self.TargetFfs = TargetFfs
        self.Status = False

    def ModifyFvExtData(self, TreeNode):
        FvExtData = b''
        if TreeNode.Data.Header.ExtHeaderOffset:
            FvExtHeader = struct2stream(TreeNode.Data.ExtHeader)
            FvExtData += FvExtHeader
        if TreeNode.Data.ExtEntryExist:
            FvExtEntry = struct2stream(TreeNode.Data.ExtEntry)
            FvExtData += FvExtEntry
        if FvExtData:
            InfoNode = TreeNode.Child[0]
            InfoNode.Data.Data = FvExtData + InfoNode.Data.Data[TreeNode.Data.ExtHeader.ExtHeaderSize:]
            InfoNode.Data.ModCheckSum()

    def ModifyTest(self, ParTree, Needed_Space):
        print('ParTree.type', ParTree.type)
        print('ParTree.Data.Name', ParTree.Data.Name)
        print('Needed_Space', Needed_Space)
        if Needed_Space > 0:
            if ParTree.type == FV_TREE or ParTree.type == SEC_FV_TREE:
                print('', ParTree.Data.Name)
                ParTree.Data.Data = b''
                Needed_Space = Needed_Space - ParTree.Data.Free_Space
                if Needed_Space < 0:
                    ParTree.Child[-1].Data.Data = b'\xff' * (-Needed_Space)
                    ParTree.Data.Free_Space = (-Needed_Space)
                    self.Status = True
                else:
                    if ParTree.type == FV_TREE:
                        self.Status = False
                    else:
                        New_Add_Len = BlockSize - Needed_Space%BlockSize
                        if New_Add_Len % BlockSize:
                            ParTree.Child[-1].Data.Data = b'\xff' * New_Add_Len
                            ParTree.Data.Free_Space = New_Add_Len
                            Needed_Space += New_Add_Len
                        else:
                            ParTree.Child.remove(ParTree.Child[-1])
                            ParTree.Data.Free_Space = 0
                        ParTree.Data.Size += Needed_Space
                        ParTree.Data.Header.Fvlength = ParTree.Data.Size
                for item in ParTree.Child:
                    if item.type == FFS_FREE_SPACE:
                        ParTree.Data.Data += item.Data.Data + item.Data.PadData
                    else:
                        ParTree.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                print('Collection')
                ParTree.Data.ModFvExt()
                ParTree.Data.ModFvSize()
                ParTree.Data.ModExtHeaderData()
                self.ModifyFvExtData(ParTree)
                ParTree.Data.ModCheckSum()
            elif ParTree.type == FFS_TREE:
                ParTree.Data.Data = b''
                print('Test')
                for item in ParTree.Child:
                    if item.Data.OriData:
                        if item.Data.ExtHeader:
                            ParTree.Data.Data += struct2stream(item.Data.Header) + struct2stream(item.Data.ExtHeader) + item.Data.OriData + item.Data.PadData
                        else:
                            ParTree.Data.Data += struct2stream(item.Data.Header)+ item.Data.OriData + item.Data.PadData
                    else:
                        if item.Data.ExtHeader:
                            ParTree.Data.Data += struct2stream(item.Data.Header) + struct2stream(item.Data.ExtHeader) + item.Data.Data + item.Data.PadData
                        else:
                            ParTree.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                ChangeSize(ParTree, -Needed_Space)
                New_Pad_Size = GetPadSize(ParTree.Data.Size, 8) 
                Delta_Pad_Size = New_Pad_Size - len(ParTree.Data.PadData)
                Needed_Space += Delta_Pad_Size
                ParTree.Data.PadData = b'\xff' * GetPadSize(ParTree.Data.Size, 8)
                ParTree.Data.ModCheckSum()
            elif ParTree.type == SECTION_TREE:
                OriData = ParTree.Data.Data
                ParTree.Data.Data = b''
                for item in ParTree.Child:
                    if item.type == SECTION_TREE and item.Data.ExtHeader and item.Data.Type != 0x02:
                        ParTree.Data.Data += struct2stream(item.Data.Header) + struct2stream(item.Data.ExtHeader) + item.Data.Data + item.Data.PadData
                    elif item.type == SECTION_TREE and item.Data.ExtHeader and item.Data.Type == 0x02:
                        ParTree.Data.Data += struct2stream(item.Data.Header) + struct2stream(item.Data.ExtHeader) + item.Data.OriData + item.Data.PadData
                    else:
                        ParTree.Data.Data += struct2stream(item.Data.Header) + item.Data.Data + item.Data.PadData
                print('len(OriData)', len(OriData))
                print(len(ParTree.Data.Data))
                if ParTree.Data.Type == 0x02:
                    ParTree.Data.Size += Needed_Space
                    print('Guid')
                    ParPath = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
                    ToolPath = os.path.join(os.path.dirname(ParPath), r'FMMTConfig.ini')
                    guidtool = GUIDTools(ToolPath).__getitem__(struct2stream(ParTree.Data.ExtHeader.SectionDefinitionGuid))
                    print('struct2stream(ParTree.Data.ExtHeader.SectionDefinitionGuid)', struct2stream(ParTree.Data.ExtHeader.SectionDefinitionGuid))
                    print('guidtool', guidtool)
                    CompressedData = guidtool.pack(ParTree.Data.Data)
                    Needed_Space = len(CompressedData) - len(ParTree.Data.OriData)
                    ParTree.Data.OriData = CompressedData
                    New_Size = ParTree.Data.HeaderLength + len(CompressedData)
                    ParTree.Data.Header.Size[0] = New_Size % (16**2)
                    ParTree.Data.Header.Size[1] = New_Size % (16**4) //(16**2)
                    ParTree.Data.Header.Size[2] = New_Size // (16**4)
                    if ParTree.NextRel:
                        New_Pad_Size = GetPadSize(New_Size, 4)
                        Delta_Pad_Size = New_Pad_Size - len(ParTree.Data.PadData)
                        ParTree.Data.PadData = b'\x00' * New_Pad_Size
                        Needed_Space += Delta_Pad_Size
                    else:
                        ParTree.Data.PadData = b''
                elif Needed_Space:
                    print('Not Guid')
                    ChangeSize(ParTree, -Needed_Space)
                    New_Pad_Size = GetPadSize(ParTree.Data.Size, 4) 
                    Delta_Pad_Size = New_Pad_Size - len(ParTree.Data.PadData)
                    Needed_Space += Delta_Pad_Size
                    ParTree.Data.PadData = b'\x00' * New_Pad_Size
                print('OriData == ParTree.Data.Data', OriData == ParTree.Data.Data)
            NewParTree = ParTree.Parent
            ROOT_TYPE = [ROOT_FV_TREE, ROOT_FFS_TREE, ROOT_SECTION_TREE, ROOT_TREE]
            if NewParTree and NewParTree.type not in ROOT_TYPE:
                self.ModifyTest(NewParTree, Needed_Space)
        else:
            self.Status = True

    def ReplaceFfs(self):
        TargetFv = self.TargetFfs.Parent
        if TargetFv.Data.Header.Attributes & EFI_FVB2_ERASE_POLARITY:
                self.NewFfs.Data.Header.State = c_uint8(
                    ~self.NewFfs.Data.Header.State)
        self.NewFfs.Data.PadData = b'\xff' * GetPadSize(self.NewFfs.Data.Size, 8)
        if self.NewFfs.Data.Size > self.TargetFfs.Data.Size:
            Needed_Space = self.NewFfs.Data.Size - self.TargetFfs.Data.Size
            if TargetFv.Data.Free_Space >= Needed_Space:
                TargetFv.Child[-1].Data.Data = b'\xff' * (TargetFv.Data.Free_Space - Needed_Space)
                TargetFv.Data.Free_Space -= Needed_Space
                Target_index = TargetFv.Child.index(self.TargetFfs)
                TargetFv.Child.remove(self.TargetFfs)
                TargetFv.insertChild(self.NewFfs, Target_index)
                TargetFv.Data.ModFvExt()
                TargetFv.Data.ModFvSize()
                TargetFv.Data.ModExtHeaderData()
                self.ModifyFvExtData(TargetFv)
                TargetFv.Data.ModCheckSum()
                self.Status = True
            else:
                if TargetFv.type == FV_TREE:
                    self.Status = False
                else:
                    New_Add_Len = BlockSize - Needed_Space%BlockSize
                    if New_Add_Len % BlockSize:
                        TargetFv.Child[-1].Data.Data = b'\xff' * New_Add_Len
                        TargetFv.Data.Free_Space = New_Add_Len
                        Needed_Space += New_Add_Len
                        TargetFv.insertChild(self.NewFfs, -1)
                    else:
                        TargetFv.Child.remove(self.TargetFfs)
                        TargetFv.Data.Free_Space = 0
                        TargetFv.insertChild(self.NewFfs)
                    TargetFv.Data.Data = b''
                    for item in TargetFv.Child:
                        if item.type == FFS_FREE_SPACE:
                            TargetFv.Data.Data += item.Data.Data + item.Data.PadData
                        else:
                            TargetFv.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                    TargetFv.Data.Size += Needed_Space
                    TargetFv.Data.Header.FvLength = TargetFv.Data.Size
                    TargetFv.Data.ModFvExt()
                    TargetFv.Data.ModFvSize()
                    TargetFv.Data.ModExtHeaderData()
                    self.ModifyFvExtData(TargetFv)
                    TargetFv.Data.ModCheckSum()
                    self.ModifyTest(TargetFv.Parent, Needed_Space)
        else:
            New_Free_Space = self.TargetFfs.Data.Size - self.NewFfs.Data.Size
            if TargetFv.Data.Free_Space:
                TargetFv.Child[-1].Data.Data += b'\xff' * New_Free_Space
                TargetFv.Data.Free_Space += New_Free_Space
                Target_index = TargetFv.Child.index(self.TargetFfs)
                TargetFv.Child.remove(self.TargetFfs)
                TargetFv.insertChild(self.NewFfs, Target_index)
                self.Status = True
            else:
                New_Free_Space_Tree = NODETREE('FREE_SPACE')
                New_Free_Space_Tree.type = FFS_FREE_SPACE
                New_Free_Space_Tree.Data = FfsNode(b'\xff' * New_Free_Space)
                TargetFv.Data.Free_Space = New_Free_Space
                TargetFv.insertChild(New_Free_Space)
                Target_index = TargetFv.Child.index(self.TargetFfs)
                TargetFv.Child.remove(self.TargetFfs)
                TargetFv.insertChild(self.NewFfs, Target_index)
                self.Status = True
            TargetFv.Data.ModFvExt()
            TargetFv.Data.ModFvSize()
            TargetFv.Data.ModExtHeaderData()
            self.ModifyFvExtData(TargetFv)
            TargetFv.Data.ModCheckSum()
        return self.Status

    def AddFfs(self):
        print('self.TargetFfs.type', self.TargetFfs.type)
        self.NewFfs.Data.PadData = b'\xff' * GetPadSize(self.NewFfs.Data.Size, 8)
        if self.TargetFfs.type == FFS_FREE_SPACE:
            TargetLen = self.NewFfs.Data.Size + len(self.NewFfs.Data.PadData) - self.TargetFfs.Data.Size - len(self.TargetFfs.Data.PadData)
            print('self.NewFfs.Data.Size', self.NewFfs.Data.Size)
            print('self.TargetFfs.Data.Size', self.TargetFfs.Data.Size)
            print(TargetLen)
            TargetFv = self.TargetFfs.Parent
            print('NewFfs', self.NewFfs.Data.Name)
            print('TargetFfs', self.TargetFfs.Data.Name)
            print('TargetFv', TargetFv.type)
            print('TargetFv Name', TargetFv.Data.Name)
            if TargetFv.Data.Header.Attributes & EFI_FVB2_ERASE_POLARITY:
                self.NewFfs.Data.Header.State = c_uint8(
                    ~self.NewFfs.Data.Header.State)
            if TargetLen < 0:
                self.Status = True
                self.TargetFfs.Data.Data = b'\xff' * (-TargetLen)
                TargetFv.Data.Free_Space = (-TargetLen)
                TargetFv.Data.ModFvExt()
                TargetFv.Data.ModExtHeaderData()
                self.ModifyFvExtData(TargetFv)
                TargetFv.Data.ModCheckSum()
                TargetFv.insertChild(self.NewFfs, -1)
                ModifyFfsType(self.NewFfs)
            elif TargetLen == 0:
                self.Status = True
                TargetFv.Child.remove(self.TargetFfs)
                TargetFv.insertChild(self.NewFfs)
                ModifyFfsType(self.NewFfs)
            else:
                if TargetFv.type == FV_TREE:
                    self.Status = False
                elif TargetFv.type == SEC_FV_TREE:
                    print('SEC_FV_TREE!')
                    New_Add_Len = BlockSize - TargetLen%BlockSize
                    print('New_Add_Len', New_Add_Len)
                    print('Child Num', len(TargetFv.Child))
                    print('TargetFv child', TargetFv.Child[-2], TargetFv.Child[-1])
                    if New_Add_Len % BlockSize:
                        self.TargetFfs.Data.Data = b'\xff' * New_Add_Len
                        self.TargetFfs.Data.Size = New_Add_Len
                        TargetLen += New_Add_Len
                        TargetFv.insertChild(self.NewFfs, -1)
                        TargetFv.Data.Free_Space = New_Add_Len
                    else:
                        TargetFv.Child.remove(self.TargetFfs)
                        TargetFv.insertChild(self.NewFfs)
                        TargetFv.Data.Free_Space = 0
                    ModifyFfsType(self.NewFfs)
                    print('Child Num', len(TargetFv.Child))
                    print('TargetFv Child', TargetFv.Child[-3], TargetFv.Child[-2], TargetFv.Child[-1])
                    print('\n')
                    TargetFv.Data.Data = b''
                    for item in TargetFv.Child:
                        if item.type == FFS_FREE_SPACE:
                            TargetFv.Data.Data += item.Data.Data + item.Data.PadData
                        else:
                            TargetFv.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                    TargetFv.Data.Size += TargetLen
                    TargetFv.Data.Header.FvLength = TargetFv.Data.Size
                    TargetFv.Data.ModFvExt()
                    TargetFv.Data.ModFvSize()
                    TargetFv.Data.ModExtHeaderData()
                    self.ModifyFvExtData(TargetFv)
                    TargetFv.Data.ModCheckSum()
                    self.ModifyTest(TargetFv.Parent, TargetLen)
        else:
            TargetLen = self.NewFfs.Data.Size + len(self.NewFfs.Data.PadData)
            TargetFv = self.TargetFfs.Parent
            print('TargetFv', TargetFv.type)
            print('TargetFv Name', TargetFv.Data.Name)
            if TargetFv.Data.Header.Attributes & EFI_FVB2_ERASE_POLARITY:
                self.NewFfs.Data.Header.State = c_uint8(
                    ~self.NewFfs.Data.Header.State)
            if TargetFv.type == FV_TREE:
                self.Status = False
            elif TargetFv.type == SEC_FV_TREE:
                print('SEC_FV_TREE!')
                New_Add_Len = BlockSize - TargetLen%BlockSize
                print('New_Add_Len', New_Add_Len)
                print('Child Num', len(TargetFv.Child))
                ChildNum = len(TargetFv.Child)
                if New_Add_Len % BlockSize:
                    New_Free_Space = NODETREE('FREE_SPACE')
                    New_Free_Space.type = FFS_FREE_SPACE
                    New_Free_Space.Data = FreeSpaceNode(b'\xff' * New_Add_Len)
                    TargetLen += New_Add_Len
                    TargetFv.Data.Free_Space = New_Add_Len
                    TargetFv.insertChild(self.NewFfs)
                    TargetFv.insertChild(New_Free_Space)
                else:
                    TargetFv.insertChild(self.NewFfs)
                ModifyFfsType(self.NewFfs)
                TargetFv.Data.Data = b''
                for item in TargetFv.Child:
                    if item.type == FFS_FREE_SPACE:
                        TargetFv.Data.Data += item.Data.Data + item.Data.PadData
                    else:
                        TargetFv.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                TargetFv.Data.Size += TargetLen
                TargetFv.Data.Header.FvLength = TargetFv.Data.Size
                TargetFv.Data.ModFvExt()
                TargetFv.Data.ModFvSize()
                TargetFv.Data.ModExtHeaderData()
                self.ModifyFvExtData(TargetFv)
                TargetFv.Data.ModCheckSum()
                self.ModifyTest(TargetFv.Parent, TargetLen)
        return self.Status