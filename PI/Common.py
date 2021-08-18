from core.NodeTree import SECTION_TREE, FV_TREE
from core.GuidTools import ModifyGuidFormat
import uuid
from PI.SectionHeader import EFI_COMMON_SECTION_HEADER2
from PI.FfsFileHeader import EFI_FFS_FILE_HEADER2, EFI_FFS_FILE_HEADER
from PI.ExtendCType import *

# ZeroGuid = uuid.UUID('{00000000-0000-0000-0000-000000000000}')
# EFI_FIRMWARE_FILE_SYSTEM2_GUID = uuid.UUID('{8C8CE578-8A3D-4f1c-9935-896185C32DD3}')
# EFI_FIRMWARE_FILE_SYSTEM3_GUID = uuid.UUID('{5473C07A-3DCB-4dca-BD6F-1E9689E7349A}')
# EFI_FFS_VOLUME_TOP_FILE_GUID = uuid.UUID('{1BA0062E-C779-4582-8566-336AE8F78F09}')

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

def GetPadSize(Size, alignment):
    if Size % alignment == 0:
        return 0
    Pad_Size = alignment - Size % alignment
    return Pad_Size

def ChangeSize(TargetTree, size_delta = 0):
    if type(TargetTree.Data.Header) == type(EFI_FFS_FILE_HEADER2()) or type(TargetTree.Data.Header) == type(EFI_COMMON_SECTION_HEADER2()):
        TargetTree.Data.Size -= size_delta
        TargetTree.Data.Header.ExtendedSize -= size_delta
    elif TargetTree.type == SECTION_TREE and TargetTree.Data.OriData:
        OriSize = TargetTree.Data.Header.SECTION_SIZE
        OriSize -= size_delta
        TargetTree.Data.Header.Size[0] = OriSize % (16**2)
        TargetTree.Data.Header.Size[1] = OriSize % (16**4) //(16**2)
        TargetTree.Data.Header.Size[2] = OriSize // (16**4)
    else:
        TargetTree.Data.Size -= size_delta
        TargetTree.Data.Header.Size[0] = TargetTree.Data.Size % (16**2)
        TargetTree.Data.Header.Size[1] = TargetTree.Data.Size % (16**4) //(16**2)
        TargetTree.Data.Header.Size[2] = TargetTree.Data.Size // (16**4)

def ModifyFfsType(TargetFfs):
    if type(TargetFfs.Data.Header) == type(EFI_FFS_FILE_HEADER()) and (TargetFfs.Data.HeaderLength + TargetFfs.Data.Size) > 0xFFFFFF:
        ExtendSize = TargetFfs.Data.Header.FFS_FILE_SIZE + 8
        New_Header = EFI_FFS_FILE_HEADER2()
        New_Header.Name = TargetFfs.Data.Header.Name
        New_Header.IntegrityCheck = TargetFfs.Data.Header.IntegrityCheck
        New_Header.Type = TargetFfs.Data.Header.Type
        New_Header.Attributes = TargetFfs.Data.Header.Attributes
        New_Header.Size = 0
        New_Header.State = TargetFfs.Data.Header.State
        New_Header.ExtendedSize = ExtendSize
        TargetFfs.Data.Header = New_Header
        TargetFfs.Data.Size = TargetFfs.Data.Header.FFS_FILE_SIZE
        TargetFfs.Data.HeaderLength = TargetFfs.Data.Header.HeaderLength
        TargetFfs.Data.ModCheckSum()
    elif type(TargetFfs.Data.Header) == type(EFI_FFS_FILE_HEADER2()) and (TargetFfs.Data.HeaderLength + TargetFfs.Data.Size) <= 0xFFFFFF:
        New_Header = EFI_FFS_FILE_HEADER()
        New_Header.Name = TargetFfs.Data.Header.Name
        New_Header.IntegrityCheck = TargetFfs.Data.Header.IntegrityCheck
        New_Header.Type = TargetFfs.Data.Header.Type
        New_Header.Attributes = TargetFfs.Data.Header.Attributes
        New_Header.Size = TargetFfs.Data.HeaderLength + TargetFfs.Data.Size
        New_Header.State = TargetFfs.Data.Header.State
        TargetFfs.Data.Header = New_Header
        TargetFfs.Data.Size = TargetFfs.Data.Header.FFS_FILE_SIZE
        TargetFfs.Data.HeaderLength = TargetFfs.Data.Header.HeaderLength
        TargetFfs.Data.ModCheckSum()
        if struct2stream(TargetFfs.Parent.Data.Header.FileSystemGuid) == EFI_FIRMWARE_FILE_SYSTEM3_GUID_BYTE:
            NeedChange = True
            for item in TargetFfs.Parent.Child:
                if type(item.Data.Header) == type(EFI_FFS_FILE_HEADER2()):
                    NeedChange = False
            if NeedChange:
                TargetFfs.Parent.Data.Header.FileSystemGuid = ModifyGuidFormat("8c8ce578-8a3d-4f1c-9935-896185c32dd3")

    if type(TargetFfs.Data.Header) == type(EFI_FFS_FILE_HEADER2()):
        TarParent = TargetFfs.Parent
        while TarParent:
            if TarParent.type == FV_TREE and struct2stream(TarParent.Data.Header.FileSystemGuid) == EFI_FIRMWARE_FILE_SYSTEM2_GUID_BYTE:
                TarParent.Data.Header.FileSystemGuid = ModifyGuidFormat("5473C07A-3DCB-4dca-BD6F-1E9689E7349A")
            TarParent = TarParent.Parent
