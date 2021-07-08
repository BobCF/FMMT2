from struct import *
from ctypes import *
from PI.ExtendCType import *

class EFI_FIRMWARE_VOLUME_HEADER(Structure):
    _fields_ = [
        ('ZeroVector',           ARRAY(c_uint8, 16)),
        ('FileSystemGuid',       GUID),
        ('FvLength',             c_uint64),
        ('Signature',            c_uint32),
        ('Attributes',           c_uint32),
        ('HeaderLength',         c_uint16),
        ('Checksum',             c_uint16),
        ('ExtHeaderOffset',      c_uint16),
        ('Reserved',             c_uint8),
        ('Revision',             c_uint8),
        ('BlockMap',             ARRAY(EFI_FV_BLOCK_MAP_ENTRY, 1)),
        ]

def Refine_FV_Header(nums):
    class EFI_FIRMWARE_VOLUME_HEADER(Structure):
        _fields_ = [
            ('ZeroVector',           ARRAY(c_uint8, 16)),
            ('FileSystemGuid',       GUID),
            ('FvLength',             c_uint64),
            ('Signature',            c_uint32),
            ('Attributes',           c_uint32),
            ('HeaderLength',         c_uint16),
            ('Checksum',             c_uint16),
            ('ExtHeaderOffset',      c_uint16),
            ('Reserved',             c_uint8),
            ('Revision',             c_uint8),
            ('BlockMap',             ARRAY(EFI_FV_BLOCK_MAP_ENTRY, nums)),
            ]
    return EFI_FIRMWARE_VOLUME_HEADER

class EFI_FIRMWARE_VOLUME_EXT_HEADER(Structure):
    _fields_ = [
        ('FvName',               GUID),
        ('ExtHeaderSize',        c_uint32)
        ]
