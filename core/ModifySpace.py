import os
from core.NodeTree import *
from core.GuidTools import GUIDTools
from core.NodeClass import *
from PI.Common import *
from PI.ExtendCType import *

BlockSize = 1000

class FfsMofify:
    def __init__(self, NewFfs, TargetFfs):
        self.NewFfs = NewFfs
        self.TargetFfs = TargetFfs
        self.Status = False

    def ModifyOffset(self, target, Delta_Offset, StopFfsName):
        if target.Data.Name != StopFfsName:
            target.Data.DOffset += Delta_Offset
            target.Data.HOffset += Delta_Offset
            for item in target.Child:
                self.ModifyOffset(item, Delta_Offset, StopFfsName)

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
                    self.Status = True
                else:
                    if ParTree.type == FV_TREE:
                        self.Status = False
                    else:
                        New_Add_Len = BlockSize - Needed_Space%BlockSize
                        if New_Add_Len % BlockSize:
                            ParTree.Child[-1].Data.Data = b'\xff' * New_Add_Len
                            Needed_Space += New_Add_Len
                        else:
                            ParTree.Child.remove(ParTree.Child[-1])
                        ParTree.Data.Size += Needed_Space
                        ParTree.Data.Header.Fvlength = ParTree.Data.Size
                for item in ParTree.Child:
                    if item.type == FFS_FREE_SPACE:
                        ParTree.Data.Data += item.Data.Data + item.Data.PadData
                    else:
                        ParTree.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
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
                    New_Pad_Size = GetPadSize(New_Size, 4) 
                    Delta_Pad_Size = New_Pad_Size - len(ParTree.Data.PadData)
                    ParTree.Data.PadData = b'\x00' * New_Pad_Size
                    Needed_Space += Delta_Pad_Size
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
        NextFfs = self.TargetFfs.NextRel
        TargetParent = self.TargetFfs.Parent
        if NextFfs and NextFfs.type == FFS_FREE_SPACE:
            # Current Fv Free space is not enough for new Ffs, need to check parent Fv
            if len(self.NewFfs.Data.Data) > len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) + len(NextFfs.Data.Data):
                Needed_Space = len(self.NewFfs.Data.Data) - len(self.TargetFfs.Data.Data) - len(self.TargetFfs.Data.PadData) - len(NextFfs.Data.Data)
                TargetParent.Child.remove(self.TargetFfs)
                New_Add_Len = BlockSize - Needed_Space%BlockSize
                if New_Add_Len % BlockSize:
                    NextFfs.Data.Data = b'\xff' * New_Add_Len
                    Needed_Space += New_Add_Len
                    TargetParent.insertChild(self.NewFfs, len(TargetParent.Child)-1)
                else:
                    TargetParent.Child.remove(NextFfs)
                    TargetParent.insertChild(self.NewFfs, -1)
                ModifyFfsType(self.NewFfs)
                TargetParent.Data.Data = b''
                for item in TargetParent.Child:
                    if item.type == FFS_FREE_SPACE:
                        TargetParent.Data.Data += item.Data.Data + item.Data.PadData
                    else:
                        TargetParent.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                TargetParent.Data.Size += Needed_Space
                TargetParent.Data.Header.FvLength = TargetParent.Data.Size
                self.ModifyTest(TargetParent.Parent, Needed_Space)
            # self.NewFfs is smaller than origin ffs
            elif len(self.NewFfs.Data.Data) <= len(self.TargetFfs.Data.Data):
                offset_delta = len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) - len(self.NewFfs.Data.Data) - len(self.NewFfs.Data.PadData)
                NextFfs.Data.Data += b'\xff'*(offset_delta)
                Target_index = TargetParent.Child.index(self.TargetFfs)
                TargetParent.Child.remove(self.TargetFfs)
                TargetParent.insertChild(self.NewFfs, Target_index)
                self.Status = True
            # self.NewFfs + NewPadData == self.TargetFfs + OriPadData
            elif len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) >= len(self.NewFfs.Data.Data) >= len(self.TargetFfs.Data.Data):
                Target_index = TargetParent.Child.index(self.TargetFfs)
                TargetParent.Child.remove(self.TargetFfs)
                TargetParent.insertChild(self.NewFfs, Target_index)
                self.Status = True
            # self.NewFfs larger than origin ffs but have enough space in current Fv.
            else:
                offset_delta = len(self.NewFfs.Data.Data) + len(self.NewFfs.Data.PadData) - len(self.TargetFfs.Data.Data) - len(self.TargetFfs.Data.PadData)
                NextFfs.Data.Data = b'\xff' * (len(NextFfs.Data.Data) - offset_delta)
                NextFfs.Data.HOffset += offset_delta
                NextFfs.Data.DOffset += offset_delta
                Target_index = TargetParent.Child.index(self.TargetFfs)
                TargetParent.Child.remove(self.TargetFfs)
                TargetParent.insertChild(self.NewFfs, Target_index)
                ModifyFfsType(self.NewFfs)
                self.Status = True
        elif NextFfs and NextFfs.type == FFS_PAD:
            # Next FFS_PAD space is not enough for new Ffs, need to check Fv freespace
            if len(self.NewFfs.Data.Data) > len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) + len(NextFfs.Data.Data) + len(NextFfs.Data.PadData):
                Needed_Space = len(self.NewFfs.Data.Data) - len(self.TargetFfs.Data.Data) - len(self.TargetFfs.Data.PadData) - len(NextFfs.Data.Data) - len(NextFfs.Data.PadData)
                if Needed_Space < TargetParent.Data.Free_Space:
                    FreeSpaceNode = TargetParent.Child[-1]
                    FreeSpaceNode.Data.Data = b'\xff' * (TargetParent.Data.Free_Space - Needed_Space)
                    Target_index = TargetParent.Child.index(self.TargetFfs)
                    TargetParent.Child.remove(self.TargetFfs)
                    TargetParent.insertChild(self.NewFfs, Target_index)
                    ModifyFfsType(self.NewFfs)
                elif Needed_Space == TargetParent.Data.Free_Space:
                    Target_index = TargetParent.Child.index(self.TargetFfs)
                    TargetParent.Child.remove(self.TargetFfs)
                    TargetParent.insertChild(self.NewFfs, Target_index)
                    TargetParent.Child.remove(TargetParent.Child[-1])
                    ModifyFfsType(self.NewFfs)
                # Current Fv Free space is not enough for new Ffs, need to check parent Fv
                else:
                    FreeSpaceNode = TargetParent.Child[-1]
                    # If current Fv have free space, first check Current Fv then parent Fv
                    if FreeSpaceNode.type == FFS_FREE_SPACE:
                        Needed_Space -= TargetParent.Data.Free_Space
                        New_Add_Len = BlockSize - Needed_Space%BlockSize
                        if New_Add_Len % BlockSize:
                            FreeSpaceNode.Data.Data = b'\xff' * New_Add_Len
                            Needed_Space += New_Add_Len
                        else:
                            TargetParent.Child.remove(FreeSpaceNode)
                        Target_index = TargetParent.Child.index(self.TargetFfs)
                        TargetParent.Child.remove(self.TargetFfs)
                        TargetParent.insertChild(self.NewFfs, Target_index)
                        ModifyFfsType(self.NewFfs)
                        TargetParent.Data.Data = b''
                        for item in TargetParent.Child:
                            if item.type == FFS_FREE_SPACE:
                                TargetParent.Data.Data += item.Data.Data + item.Data.PadData
                            else:
                                TargetParent.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                        TargetParent.Data.Size += Needed_Space
                        TargetParent.Data.Header.FvLength = TargetParent.Data.Size
                        self.ModifyTest(TargetParent.Parent, Needed_Space)
                    # If current Fv do not have free space, check parent free space
                    else:
                        New_Add_Len = BlockSize - Needed_Space%BlockSize
                        if New_Add_Len < struct2stream(self.NewFfs.Data.Header):
                            TargetParent.Child[-1].Data.PadData += b'\xff' * New_Add_Len
                        else:
                            if New_Add_Len % BlockSize:
                                New_Free_Space = NODETREE(PADVECTOR)
                                New_Free_Space.type = FFS_FREE_SPACE
                                New_Free_Space.Data = FfsNode(New_Add_Len)
                                New_Free_Space.Data.Data = b'\xff' * New_Add_Len
                                Needed_Space += New_Add_Len
                                TargetParent.insertChild(New_Free_Space, -1)
                            else:
                                TargetParent.Child.remove(FreeSpaceNode)
                            Target_index = TargetParent.Child.index(self.TargetFfs)
                            TargetParent.Child.remove(self.TargetFfs)
                            TargetParent.insertChild(self.NewFfs, Target_index)
                            ModifyFfsType(self.NewFfs)
                            TargetParent.Data.Data = b''
                            for item in TargetParent.Child:
                                if item.type == FFS_FREE_SPACE:
                                    TargetParent.Data.Data += item.Data.Data + item.Data.PadData
                                else:
                                    TargetParent.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                            TargetParent.Data.Size += Needed_Space
                            TargetParent.Data.Header.FvLength = TargetParent.Data.Size
                            self.ModifyTest(TargetParent.Parent, Needed_Space)
            # self.NewFfs is smaller than origin ffs
            elif len(self.NewFfs.Data.Data) <= len(self.TargetFfs.Data.Data):
                offset_delta = len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) - len(self.NewFfs.Data.Data) - len(self.NewFfs.Data.PadData)
                NextFfs.Data.Data += b'\xff' * (offset_delta)
                NextFfs.Data.HOffset -= offset_delta
                NextFfs.Data.DOffset -= offset_delta
                NextFfs.Data.Size += offset_delta
                ChangeSize(NextFfs, -offset_delta)
                Target_index = TargetParent.Child.index(self.TargetFfs)
                TargetParent.Child.remove(self.TargetFfs)
                TargetParent.insertChild(self.NewFfs, Target_index)
                self.Status = True
            # self.NewFfs + NewPadData == self.TargetFfs + OriPadData
            elif len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) >= len(self.NewFfs.Data.Data) >= len(self.TargetFfs.Data.Data):
                Target_index = TargetParent.Child.index(self.TargetFfs)
                TargetParent.Child.remove(self.TargetFfs)
                TargetParent.insertChild(self.NewFfs, Target_index)
                self.Status = True
            # self.NewFfs larger than origin ffs but have enough space in Next FFS PAD.
            else:
                offset_delta = len(self.NewFfs.Data.Data) + len(self.NewFfs.Data.PadData) - len(self.TargetFfs.Data.Data) - len(self.TargetFfs.Data.PadData)
                # Next FFS PAD Data space is enough for self.NewFfs
                if (len(NextFfs.Data.Data) - offset_delta) >= 0:
                    NextFfs.Data.Data = b'\xff' * (len(NextFfs.Data.Data) - offset_delta)
                    NextFfs.Data.HOffset += offset_delta
                    NextFfs.Data.DOffset += offset_delta
                    NextFfs.Data.Size -= offset_delta
                    ChangeSize(NextFfs, offset_delta)
                    Target_index = TargetParent.Child.index(self.TargetFfs)
                    TargetParent.Child.remove(self.TargetFfs)
                    TargetParent.insertChild(self.NewFfs, Target_index)
                    ModifyFfsType(self.NewFfs)
                # The left free space is not enough for a new FFS PAD
                else:
                    self.NewFfs.Data.PadData += b'\xff' * (offset_delta - len(NextFfs.Data.Data))
                    Target_index = TargetParent.Child.index(self.TargetFfs)
                    TargetParent.Child.remove(self.TargetFfs)
                    TargetParent.insertChild(self.NewFfs, Target_index)
                    ModifyFfsType(self.NewFfs)
                    TargetParent.Child.remove(NextFfs)
                self.Status = True
        else:
            # Target Ffs space is not enough for new Ffs, need to check Fv freespace
            if len(self.NewFfs.Data.Data) > len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData):
                Needed_Space = len(self.NewFfs.Data.Data) - len(self.TargetFfs.Data.Data) - len(self.TargetFfs.Data.PadData)
                if Needed_Space < TargetParent.Data.Free_Space:
                    FreeSpaceNode = TargetParent.Child[-1]
                    FreeSpaceNode.Data.Data = b'\xff' * (TargetParent.Data.Free_Space - Needed_Space)
                    Target_index = TargetParent.Child.index(self.TargetFfs)
                    TargetParent.Child.remove(self.TargetFfs)
                    TargetParent.insertChild(self.NewFfs, Target_index)
                    ModifyFfsType(self.NewFfs)
                    self.Status = True
                elif Needed_Space == TargetParent.Data.Free_Space:
                    Target_index = TargetParent.Child.index(self.TargetFfs)
                    TargetParent.Child.remove(self.TargetFfs)
                    TargetParent.insertChild(self.NewFfs, Target_index)
                    ModifyFfsType(self.NewFfs)
                    TargetParent.Child.remove(TargetParent.Child[-1])
                    self.Status = True
                # Current Fv Free space is not enough for new Ffs, need to check parent Fv
                else:
                    FreeSpaceNode = TargetParent.Child[-1]
                    if FreeSpaceNode.type == FFS_FREE_SPACE:
                        Needed_Space -= TargetParent.Data.Free_Space
                        New_Add_Len = BlockSize - Needed_Space%BlockSize
                        if New_Add_Len % BlockSize:
                            FreeSpaceNode.Data.Data = b'\xff' * New_Add_Len
                            Needed_Space += New_Add_Len
                        else:
                            TargetParent.Child.remove(FreeSpaceNode)
                        Target_index = TargetParent.Child.index(self.TargetFfs)
                        TargetParent.Child.remove(self.TargetFfs)
                        TargetParent.insertChild(self.NewFfs, Target_index)
                        ModifyFfsType(self.NewFfs)
                        TargetParent.Data.Data = b''
                        for item in TargetParent.Child:
                            if item.type == FFS_FREE_SPACE:
                                TargetParent.Data.Data += item.Data.Data + item.Data.PadData
                            else:
                                TargetParent.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                        TargetParent.Data.Size += Needed_Space
                        TargetParent.Data.Header.FvLength = TargetParent.Data.Size
                        self.ModifyTest(TargetParent.Parent, Needed_Space)
                    else:
                        New_Add_Len = BlockSize - Needed_Space%BlockSize
                        if New_Add_Len < struct2stream(self.NewFfs.Data.Header):
                            TargetParent.Child[-1].Data.PadData += b'\xff' * New_Add_Len
                        else:
                            if New_Add_Len % BlockSize:
                                New_Free_Space = NODETREE(PADVECTOR)
                                New_Free_Space.type = FFS_FREE_SPACE
                                New_Free_Space.Data = FfsNode(New_Add_Len)
                                New_Free_Space.Data.Data = b'\xff' * New_Add_Len
                                Needed_Space += New_Add_Len
                                TargetParent.insertChild(New_Free_Space, -1)
                            else:
                                TargetParent.Child.remove(FreeSpaceNode)
                            Target_index = TargetParent.Child.index(self.TargetFfs)
                            TargetParent.Child.remove(self.TargetFfs)
                            TargetParent.insertChild(self.NewFfs, Target_index)
                            ModifyFfsType(self.NewFfs)
                            TargetParent.Data.Data = b''
                            for item in TargetParent.Child:
                                if item.type == FFS_FREE_SPACE:
                                    TargetParent.Data.Data += item.Data.Data + item.Data.PadData
                                else:
                                    TargetParent.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                            TargetParent.Data.Size += Needed_Space
                            TargetParent.Data.Header.FvLength = TargetParent.Data.Size
                            self.ModifyTest(TargetParent.Parent, Needed_Space)
            elif len(self.NewFfs.Data.Data) > len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) - self.TargetFfs.Data.Header.HeaderLength:
                offset_delta = len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) - len(self.NewFfs.Data.Data)
                self.NewFfs.Data.Data += b'\xff' * (offset_delta)
                self.NewFfs.Data.PadData = b''
                self.NewFfs.Data.Size += offset_delta
                ChangeSize(NextFfs, -offset_delta)
                Target_index = TargetParent.Child.index(self.TargetFfs)
                TargetParent.Child.remove(self.TargetFfs)
                TargetParent.insertChild(self.NewFfs, Target_index)
                self.Status = True
            else:
                offset_delta = len(self.TargetFfs.Data.Data) + len(self.TargetFfs.Data.PadData) - len(self.NewFfs.Data.Data)
                self.NewFfs_pad = NODETREE(PADVECTOR)
                self.NewFfs_pad.type = FFS_PAD
                self.NewFfs_pad.Data = FfsNode(b'\xff'* offset_delta)
                self.NewFfs_pad.Data.Size = offset_delta
                ChangeSize(NextFfs)
                Target_index = TargetParent.Child.index(self.TargetFfs)
                TargetParent.Child.remove(self.TargetFfs)
                TargetParent.insertChild(self.NewFfs, Target_index)
                TargetParent.insertChild(self.NewFfs_pad, Target_index+1)
                self.Status = True
        return self.Status

    def AddFfs(self):
        print('self.TargetFfs.type', self.TargetFfs.type)
        if self.TargetFfs.type == FFS_FREE_SPACE:   
            TargetLen = self.NewFfs.Data.Size - self.TargetFfs.Data.Size
            print('self.NewFfs.Data.Size', self.NewFfs.Data.Size)
            print('self.TargetFfs.Data.Size', self.TargetFfs.Data.Size)
            print(TargetLen)
            TargetFv = self.TargetFfs.Parent
            print('NewFfs', self.NewFfs.Data.Name)
            print('TargetFfs', self.TargetFfs.Data.Name)
            print('TargetFv', TargetFv.type)
            print('TargetFv Name', TargetFv.Data.Name)
            if TargetLen < 0:
                self.Status = True
                self.TargetFfs.Data.Data = b'\xff' * (-TargetLen)
                TargetFv.insertChild(self.NewFfs, -2)
                ModifyFfsType(self.NewFfs)
            elif TargetLen == 0:
                self.Status = True
                TargetFv.Child.remove(self.TargetFfs)
                TargetFv.insertChild(self.NewFfs, -1)
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
                    ChildNum = len(TargetFv.Child)
                    if New_Add_Len % BlockSize:
                        self.TargetFfs.Data.Data = b'\xff' * New_Add_Len
                        TargetLen += New_Add_Len
                        TargetFv.insertChild(self.NewFfs, ChildNum-1)
                    else:
                        TargetFv.Child.remove(self.TargetFfs)
                        TargetFv.insertChild(self.NewFfs, -1)
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
                    self.ModifyTest(TargetFv.Parent, TargetLen)
        else:
            TargetLen = self.NewFfs.Data.Size
            TargetFv = self.TargetFfs.Parent
            print('TargetFv', TargetFv.type)
            print('TargetFv Name', TargetFv.Data.Name)
            if TargetFv.type == FV_TREE:
                self.Status = False
            elif TargetFv.type == SEC_FV_TREE:
                print('SEC_FV_TREE!')
                New_Add_Len = BlockSize - TargetLen%BlockSize
                print('New_Add_Len', New_Add_Len)
                print('Child Num', len(TargetFv.Child))
                ChildNum = len(TargetFv.Child)
                if New_Add_Len < struct2stream(self.NewFfs.Data.Header):
                    TargetFv.insertChild(self.NewFfs, -1)
                    TargetFv.Child[-1].Data.PadData += b'\xff' * New_Add_Len
                else:
                    if New_Add_Len % BlockSize:
                        New_Free_Space = NODETREE(PADVECTOR)
                        New_Free_Space.type = FFS_FREE_SPACE
                        New_Free_Space.Data = FfsNode(New_Add_Len)
                        New_Free_Space.Data.Data = b'\xff' * New_Add_Len
                        TargetLen += New_Add_Len
                        TargetFv.insertChild(self.NewFfs, -1)
                        TargetFv.insertChild(New_Free_Space, -1)
                    else:
                        TargetFv.insertChild(self.NewFfs, -1)
                ModifyFfsType(self.NewFfs)
                TargetFv.Data.Data = b''
                for item in TargetFv.Child:
                    if item.type == FFS_FREE_SPACE:
                        TargetFv.Data.Data += item.Data.Data + item.Data.PadData
                    else:
                        TargetFv.Data.Data += struct2stream(item.Data.Header)+ item.Data.Data + item.Data.PadData
                TargetFv.Data.Size += TargetLen
                TargetFv.Data.Header.FvLength = TargetFv.Data.Size
                self.ModifyTest(TargetFv.Parent, TargetLen)
        return self.Status