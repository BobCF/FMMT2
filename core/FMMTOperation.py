## @file
# This file is used to parser the image as a tree.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent

##
from core.FMMTParser import *
from core.ModifySpace import *

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
    if outputfile:
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
            Free_Space_Data = Delete_Ffs.Data.Size * b'\xff' + Delete_Ffs.Data.PadData
            if Delete_Fv.Data.Free_Space:
                Delete_Fv.Child[-1].Data.Data += Free_Space_Data
            else:
                New_Free_Space_Info = FfsNode(Free_Space_Data)
                New_Free_Space_Info.Data = Free_Space_Data
                New_Ffs_Tree = NODETREE(New_Free_Space_Info.Name)
                New_Ffs_Tree.type = FFS_FREE_SPACE
                New_Ffs_Tree.Data = New_Free_Space_Info
                Delete_Fv.insertChild(New_Ffs_Tree)
            Delete_Fv.Child.remove(Delete_Ffs)
        FmmtParser.CompressData(Delete_Fv)
    # 4. Data Encapsultion
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
    NewFmmtParser = FMMTParser(newffsfile, ROOT_FFS_TREE)
    # FindSpace = False
    # 3. Data Modify
    for TargetFv in FmmtParser.WholeFvTree.Findlist:
        TargetFfsPad = TargetFv.Child[-1]
        if TargetFfsPad.type == FFS_FREE_SPACE:
            NewFmmtParser.ParserFromRoot(NewFmmtParser.WholeFvTree, new_ffs_data, TargetFfsPad.Data.HOffset)
        else:
            NewFmmtParser.ParserFromRoot(NewFmmtParser.WholeFvTree, new_ffs_data, TargetFfsPad.Data.HOffset+TargetFfsPad.Data.Size)
        print('NewFmmtParser.WholeFvTree.Child', NewFmmtParser.WholeFvTree.Child[0].Data.Name)
        print('TargetFfsPad', TargetFfsPad.Data.Name)
        FfsMod = FfsMofify(NewFmmtParser.WholeFvTree.Child[0], TargetFfsPad)
        Status = FfsMod.AddFfs()
        print('Status', Status)
    # 4. Data Encapsultion
    if Status:
        FmmtParser.Encapsulation(FmmtParser.WholeFvTree, False)
        with open(outputfile, "wb") as f:
            f.write(FmmtParser.FinalData)

def ReplaceFfs(inputfile, Ffs_name, newffsfile, outputfile, Fv_name=None):
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
    if Fv_name:
        for item in FmmtParser.WholeFvTree.Findlist:
            if item.Parent.key != Fv_name and item.Parent.Data.Name != Fv_name:
                FmmtParser.WholeFvTree.Findlist.remove(item)
    if FmmtParser.WholeFvTree.Findlist != []:
        for TargetFfs in FmmtParser.WholeFvTree.Findlist:
            FfsMod = FfsMofify(newFmmtParser.WholeFvTree.Child[0], TargetFfs)
            Status = FfsMod.ReplaceFfs()
            print('Status', Status)
    # 4. Data Encapsultion
    if Status:
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