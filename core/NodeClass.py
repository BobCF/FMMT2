from PI.FvHeader import *
from PI.FfsFileHeader import *
from PI.SectionHeader import *
from PI.ExtendCType import *
import uuid

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
HeaderType = [0x01, 0x02, 0x14, 0x15, 0x18]

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
            self.ExtEntryOffset = self.Header.ExtHeaderOffset + 20
            if self.ExtHeader.ExtHeaderSize != 20:
                self.ExtEntryExist = 1
                self.ExtEntry = EFI_FIRMWARE_VOLUME_EXT_ENTRY.from_buffer_copy(buffer[self.ExtEntryOffset:])
                self.ExtTypeExist = 1
                if self.ExtEntry.ExtEntryType == 0x01:
                    nums = (self.ExtEntry.ExtEntrySize - 8) // 16
                    self.ExtEntry = Refine_FV_EXT_ENTRY_OEM_TYPE_Header(nums).from_buffer_copy(buffer[self.ExtEntryOffset:])
                elif self.ExtEntry.ExtEntryType == 0x02:
                    nums = self.ExtEntry.ExtEntrySize - 20
                    self.ExtEntry = Refine_FV_EXT_ENTRY_GUID_TYPE_Header(nums).from_buffer_copy(buffer[self.ExtEntryOffset:])
                elif self.ExtEntry.ExtEntryType == 0x03:
                    self.ExtEntry = EFI_FIRMWARE_VOLUME_EXT_ENTRY_USED_SIZE_TYPE.from_buffer_copy(buffer[self.ExtEntryOffset:])
                else:
                    self.ExtTypeExist = 0
            else:
                self.ExtEntryExist = 0
        self.Size = self.Header.FvLength
        self.HeaderLength = self.Header.HeaderLength
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        if self.Header.Signature != 1213613663:
            print('Invalid! Fv Header Signature {} is not "_FVH".'.format(self.Header.Signature))
            with open(str(self.Name)+'.fd', "wb") as f:
                f.write(struct2stream(self.Header))
            assert False
        self.PadData = b''
        self.Free_Space = 0
        self.ModCheckSum()

    def ModCheckSum(self):
        # Fv Header Sums to 0.
        Header = struct2stream(self.Header)[::-1]
        Size = self.HeaderLength // 2
        Sum = 0
        for i in range(Size):
            Sum += int(Header[i*2: i*2 + 2].hex(), 16)
        if Sum & 0xffff:
            self.Header.Checksum = int(hex(0x10000 - int(hex(Sum - self.Header.Checksum)[-4:], 16)), 16)

    def ModFvExt(self):
        # If used space changes and self.ExtEntry.UsedSize exists, self.ExtEntry.UsedSize need to be changed.
        if self.Header.ExtHeaderOffset and self.ExtEntryExist and self.ExtTypeExist and self.ExtEntry.Hdr.ExtEntryType == 0x03:
            self.ExtEntry.UsedSize = self.Header.FvLength - self.Free_Space

    def ModFvSize(self):
        # If Fv Size changed, self.Header.FvLength and self.Header.BlockMap[i].NumBlocks need to be changed.
        BlockMapNum = len(self.Header.BlockMap)
        for i in range(BlockMapNum):
            if self.Header.BlockMap[i].Length:
                self.Header.BlockMap[i].NumBlocks = self.Header.FvLength // self.Header.BlockMap[i].Length

    def ModExtHeaderData(self):
        if self.Header.ExtHeaderOffset:
            ExtHeaderData = struct2stream(self.ExtHeader)
            ExtHeaderDataOffset = self.Header.ExtHeaderOffset - self.HeaderLength
            self.Data = self.Data[:ExtHeaderDataOffset] + ExtHeaderData + self.Data[ExtHeaderDataOffset+20:]
        if self.Header.ExtHeaderOffset and self.ExtEntryExist:
            ExtHeaderEntryData = struct2stream(self.ExtEntry)
            ExtHeaderEntryDataOffset = self.Header.ExtHeaderOffset + 20 - self.HeaderLength
            self.Data = self.Data[:ExtHeaderEntryDataOffset] + ExtHeaderEntryData + self.Data[ExtHeaderEntryDataOffset+len(ExtHeaderEntryData):]

class FfsNode:
    def __init__(self, buffer: bytes):
        self.Header = EFI_FFS_FILE_HEADER.from_buffer_copy(buffer)
        # self.Attributes = unpack("<B", buffer[21:22])[0]
        if self.Header.Size != 0 and self.Header.Attributes == 0x01:
            print('Error Ffs Header! Ffs Header Size and Attributes is not matched!')
        if self.Header.Size == 0 and self.Header.Attributes == 0x01:
            self.Header = EFI_FFS_FILE_HEADER2.from_buffer_copy(buffer)
        self.Name = uuid.UUID(bytes_le=struct2stream(self.Header.Name))
        self.UiName = b''
        self.Version = b''
        self.Size = self.Header.FFS_FILE_SIZE
        self.HeaderLength = self.Header.HeaderLength
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.Data = b''
        self.PadData = b''

    def ModCheckSum(self):
        HeaderData = struct2stream(self.Header)
        HeaderSum = 0
        for item in HeaderData:
            HeaderSum += item
        HeaderSum -= self.Header.State
        HeaderSum -= self.Header.IntegrityCheck.Checksum.File
        if HeaderSum & 0xff:
            Header = self.Header.IntegrityCheck.Checksum.Header + 0x100 - int(hex(HeaderSum)[-2:], 16)
            self.Header.IntegrityCheck.Checksum.Header = int(hex(Header)[-2:], 16)

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
            self.ExtHeader = self.GetExtHeader(self.Header.Type, buffer[self.Header.Common_Header_Size():], (self.Header.SECTION_SIZE-self.Header.Common_Header_Size()))
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

    def GetExtHeader(self, Type, buffer:bytes, nums = 0):
        if Type == 0x01:
            return EFI_COMPRESSION_SECTION.from_buffer_copy(buffer)
        elif Type == 0x02:
            return EFI_GUID_DEFINED_SECTION.from_buffer_copy(buffer)
        elif Type == 0x14:
            return Get_VERSION_Header((nums - 2)//2).from_buffer_copy(buffer)
        elif Type == 0x15:
            return Get_USER_INTERFACE_Header(nums//2).from_buffer_copy(buffer)
        elif Type == 0x18:
            return EFI_FREEFORM_SUBTYPE_GUID_SECTION.from_buffer_copy(buffer)

class FreeSpaceNode:
    def __init__(self, buffer: bytes):
        self.Name = 'Free_Space'
        self.Data = buffer
        self.Size = len(buffer)
        self.HOffset = 0
        self.DOffset = 0
        self.ROffset = 0
        self.PadData = b''