from struct import *
from ctypes import *

class GUID(Structure):
    _pack_ = 1
    _fields_ = [
        ('Guid1',            c_uint32),
        ('Guid2',            c_uint16),
        ('Guid3',            c_uint16),
        ('Guid4',            ARRAY(c_uint8, 8)),
    ]

    def from_list(self, listformat):
        self.Guid1 = listformat[0]
        self.Guid2 = listformat[1]
        self.Guid3 = listformat[2]
        for i in range(8):
            self.Guid4[i] = listformat[i+3]

    def __cmp__(self, otherguid):
        if not isinstance(otherguid, GUID):
            return 'Input is not the GUID instance!'
        rt = False
        if self.Guid1 == otherguid.Guid1 and self.Guid2 == otherguid.Guid2 and self.Guid3 == otherguid.Guid3:
            rt = True
            for i in range(8):
                rt = rt & (self.Guid4[i] == otherguid.Guid4[i])
        return rt

class EFI_FV_BLOCK_MAP_ENTRY(Structure):
    _pack_ = 1
    _fields_ = [
        ('NumBlocks',            c_uint32),
        ('Length',               c_uint32),
    ]

def struct2stream(s):
    length = sizeof(s)
    p = cast(pointer(s), POINTER(c_char * length))
    return p.contents.raw
