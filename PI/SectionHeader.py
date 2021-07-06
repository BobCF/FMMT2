from struct import *
from ctypes import *
from PI.CommonType import *

EFI_COMMON_SECTION_HEADER_LEN = 4
EFI_COMMON_SECTION_HEADER2_LEN = 8

class EFI_COMMON_SECTION_HEADER(Structure):
    _pack_ = 1
    _fields_ = [
        ('Size',                     ARRAY(c_uint8, 3)),
        ('Type',                     c_uint8),
    ]

    @property
    def SECTION_SIZE(self):
        return self.Size[0] | self.Size[1] << 8 | self.Size[2] << 16
    
    def Common_Header_Size(self):
        return 4

class EFI_COMMON_SECTION_HEADER2(Structure):
    _pack_ = 1
    _fields_ = [
        ('Size',                     ARRAY(c_uint8, 3)),
        ('Type',                     c_uint8),
        ('ExtendedSize',             c_uint32),
    ]

    @property
    def SECTION_SIZE(self):
        return self.ExtendedSize

    def Common_Header_Size(self):
        return 8

class EFI_COMPRESSION_SECTION(Structure):
    _pack_ = 1
    _fields_ = [
        ('UncompressedLength',       c_uint32),
        ('CompressionType',          c_uint8),
    ]

    def ExtHeaderSize(self):
        return 5

class EFI_FREEFORM_SUBTYPE_GUID_SECTION(Structure):
    _pack_ = 1
    _fields_ = [
        ('SubTypeGuid',              GUID),
    ]

    def ExtHeaderSize(self):
        return 16

class EFI_GUID_DEFINED_SECTION(Structure):
    _pack_ = 1
    _fields_ = [
        ('SectionDefinitionGuid',    GUID),
        ('DataOffset',               c_uint16),
        ('Attributes',               c_uint16),
    ]

    def ExtHeaderSize(self):
        return 20

class EFI_SECTION_USER_INTERFACE(Structure):
    _pack_ = 1
    _fields_ = [
        ('FileNameString',           c_uint16),
    ]

    def ExtHeaderSize(self):
        return 2

class EFI_SECTION_VERSION(Structure):
    _pack_ = 1
    _fields_ = [
        ('BuildNumber',              c_uint16),
        ('VersionString',            c_uint16),
    ]

    def ExtHeaderSize(self):
        return 4
