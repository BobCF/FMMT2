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
        self.UiName = b''
        self.Version = b''
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