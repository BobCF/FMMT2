## @file
# This file is used to parser the image as a tree.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent

##
from core.FMMTParser import *

global Fv_count
Fv_count = 0

def SaveTreeInfo(TreeInfo, outputname):
    with open(outputname, "w") as f:
        for item in TreeInfo:
            f.writelines(item + '\n')

# The ROOT_TYPE can be 'ROOT_TREE', 'ROOT_FV_TREE', 'ROOT_FFS_TREE', 'ROOT_SECTION_TREE'
def ParserFile(inputfile, outputfile, ROOT_TYPE):
    # 1. Data Prepare
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TYPE)
    print("\nParserData Start!\n")
    # 2. DataTree Create
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    # 3. Log Output
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Parser_{}.log".format(os.path.basename(inputfile)))
    # 4. Data Encapsultion
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
            FmmtParser.CompressData(item.Parent)
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Delete_{}.log".format(os.path.basename(inputfile)))
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

def DeleteFfs(inputfile, TargetFfs_name, outputfile, Fv_name=None):
    # 1. Data Prepare
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    # 2. DataTree Create
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    # 3. Data Modify
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
                    ChangeSize(LastFfs, -AppendSize)
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
                    ChangeSize(LastFfs, -AppendSize)
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
                    ChangeSize(Delete_Ffs, -AppendSize)
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
                    ChangeSize(Delete_Ffs, -AppendSize)
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
        FmmtParser.CompressData(Delete_Fv)
    # 4. Log Output
    FmmtParser.BinaryInfo = []
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Delete_{}.log".format(os.path.basename(inputfile)))
    # 5. Data Encapsultion
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

def AddNewFfs(inputfile, Fv_name, newffsfile, outputfile):
    # 1. Data Prepare
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    # 2. DataTree Create
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    # Get Target Fv and Target Ffs_Pad
    FmmtParser.WholeFvTree.FindNode(Fv_name, FmmtParser.WholeFvTree.Findlist)
    # Create new ffs Tree
    with open(newffsfile, "rb") as f:
        new_ffs_data = f.read()
    NewFmmtParser = FMMTParser(newffsfile, FV_TREE)
    FindSpace = False
    # 3. Data Modify
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
                FmmtParser.CompressData(TargetFv)
        else:
            print("TargetFv does not have enough space for adding!")
            break
    # 4. Log Output
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Add_.log".format(os.path.basename(inputfile)))
    # 5. Data Encapsultion
    FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
    with open(outputfile, "wb") as f:
        f.write(FmmtParser.FinalData)

def ReplaceFfs(inputfile, Ffs_name, newffsfile, outputfile):
    # 1. Data Prepare
    with open(inputfile, "rb") as f:
        whole_data = f.read()
    FmmtParser = FMMTParser(inputfile, ROOT_TREE)
    # 2. DataTree Create
    FmmtParser.ParserFromRoot(FmmtParser.WholeFvTree, whole_data)
    with open(newffsfile, "rb") as f:
        new_ffs_data = f.read()
    newFmmtParser = FMMTParser(newffsfile, FV_TREE)
    newFmmtParser.ParserFromRoot(newFmmtParser.WholeFvTree, new_ffs_data)
    # 3. Data Modify
    new_ffs = newFmmtParser.WholeFvTree.Child[0]
    new_ffs.Data.PadData = GetPadSize(new_ffs.Data.Size, 8) * b'\xff'
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
                    FmmtParser.CompressData(TargetParent)
                elif len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) >= len(new_ffs.Data.Data) >= len(TargetFfs.Data.Data):
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.CompressData(TargetParent)
                else:
                    offset_delta = len(new_ffs.Data.Data) + len(new_ffs.Data.PadData) - len(TargetFfs.Data.Data) - len(TargetFfs.Data.PadData)
                    NextFfs.Data.Data = b'\xff' * (len(NextFfs.Data.Data) - offset_delta)
                    NextFfs.Data.HOffset += offset_delta
                    NextFfs.Data.DOffset += offset_delta
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.CompressData(TargetParent)
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
                    ChangeSize(NextFfs, -offset_delta)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.CompressData(TargetParent)
                elif len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) >= len(new_ffs.Data.Data) >= len(TargetFfs.Data.Data):
                    print(newFmmtParser.WholeFvTree.Child[0].key)
                    print('TargetFfs.Pad', TargetFfs.Data.PadData)
                    print('new_ffs.Pad', new_ffs.Data.PadData)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.CompressData(TargetParent)
                else:
                    offset_delta = len(new_ffs.Data.Data) + len(new_ffs.Data.PadData) - len(TargetFfs.Data.Data) - len(TargetFfs.Data.PadData)
                    NextFfs.Data.Data = b'\xff' * (len(NextFfs.Data.Data) - offset_delta)
                    NextFfs.Data.HOffset += offset_delta
                    NextFfs.Data.DOffset += offset_delta
                    NextFfs.Data.Size -= offset_delta
                    ChangeSize(NextFfs, offset_delta)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.CompressData(TargetParent)
            else:
                if len(new_ffs.Data.Data) > len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData):
                    print('The new ffs is too large, could not replace!!')
                    break
                elif len(new_ffs.Data.Data) > len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - TargetFfs.Data.Header.HeaderLength:
                    offset_delta = len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - len(new_ffs.Data.Data)
                    new_ffs.Data.Data += b'\xff' * (offset_delta)
                    new_ffs.Data.PadData = b''
                    new_ffs.Data.Size += offset_delta
                    ChangeSize(NextFfs, -offset_delta)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    FmmtParser.CompressData(TargetParent)
                else:
                    offset_delta = len(TargetFfs.Data.Data) + len(TargetFfs.Data.PadData) - len(new_ffs.Data.Data)
                    new_ffs_pad = NODETREE(PADVECTOR)
                    new_ffs_pad.type = FFS_PAD
                    new_ffs_pad.Data = FfsNode(b'\xff'* offset_delta)
                    new_ffs_pad.Data.Size = offset_delta
                    ChangeSize(NextFfs)
                    TargetParent = TargetFfs.Parent
                    Target_index = TargetParent.Child.index(TargetFfs)
                    TargetParent.Child.remove(TargetFfs)
                    TargetParent.insertChild(new_ffs, Target_index)
                    TargetParent.insertChild(new_ffs_pad, Target_index+1)
                    FmmtParser.CompressData(TargetParent)
    # 4. Log Output
    FmmtParser.WholeFvTree.parserTree(FmmtParser.BinaryInfo)
    SaveTreeInfo(FmmtParser.BinaryInfo, "Log\Replace_{}.log".format(os.path.basename(inputfile)))
    # 5. Data Encapsultion
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