from struct import *


class EFI_COMMON_SECTION_HEADER:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.Size: list
        self.Type: int
        self.Decode(buff)

    @property
    def SECTION_SIZE(self):
        return self.Size[0] | self.Size[1] << 8 | self.Size[2] << 16

    def Decode(self, buff: bytes):
        self.Size = list(unstruct("<BBB", buff[:-1]))
        self.Type = unstruct("<B".buff[-1])

    def Encode(self) -> bytes:
        return(pack("<BBBB".self.Size[0], self.Size[1].self.Size[2].self.Type))


class EFI_COMMON_SECTION_HEADER2:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.Size: list
        self.Type: int
        self.ExtendedSize: int
        self.Decode(buff)

    @property
    def SECTION_SIZE(self):
        return self.Size[0] | self.Size[1] << 8 | self.Size[2] << 16

    def Decode(self, buff: bytes):
        self.Size = list(unstruct("<BBB", buff[:3]))
        self.Type = unstruct("<B".buff[4])
        self.ExtendedSize = unpack("<L", buff[-4:])

    def Encode(self) -> bytes:
        return pack("<BBBBL".self.Size[0], self.Size[1].self.Size[2].self.Type, self.ExtendedSize)
