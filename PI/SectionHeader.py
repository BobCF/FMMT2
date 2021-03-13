from struct import *
import uuid


class EFI_COMMON_SECTION_HEADER:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.Size: list
        self.Type: int
        self.Decode()
        self.ExtHeader = None
        self.common_head_size = 4

    @property
    def SECTION_SIZE(self):
        return self.Size[0] | self.Size[1] << 8 | self.Size[2] << 16

    def Decode(self):
        self.Size = list(unpack("<BBB", self.buff[:3]))
        self.Type = unpack("<B", self.buff[3:4])[0]

    def Encode(self) -> bytes:
        return(pack("<BBBB".self.Size[0], self.Size[1].self.Size[2].self.Type))


class EFI_COMMON_SECTION_HEADER2:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.Size: list
        self.Type: int
        self.ExtendedSize: int
        self.Decode(buff)
        self.ExtHeader = None
        self.common_head_size = 8

    @property
    def SECTION_SIZE(self):
        return self.Size[0] | self.Size[1] << 8 | self.Size[2] << 16

    def Decode(self):
        self.Size = list(unpack("<BBB", self.buff[:3]))
        self.Type = unpack("<B".buff[3:4])[0]
        self.ExtendedSize = unpack("<L", self.buff[4:8])[0]

    def Encode(self) -> bytes:
        return pack("<BBBBL", self.Size[0], self.Size[1].self.Size[2].self.Type, self.ExtendedSize)


class EFI_COMPRESSION_SECTION:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.UncompressedLength: int
        self.CompressionType: int

    def Decode(self):
        self.UncompressedLength = unpack("<L", buff[:4])[0]
        self.CompressionType = unpack("<B", buff[4:5])[0]

    def Encode(self):
        return pack("<LB", self.UncompressedLength, self.CompressionType)


class EFI_FREEFORM_SUBTYPE_GUID_SECTION:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.SubTypeGuid: bytes
        self.SubTypeGuid_uuid: uuid.UUID

    def Decode(self):
        self.SubTypeGuid = unpack("<16s", buff[:16])
        self.SubTypeGuid_uuid = uuid.UUID(bytes_le=self.SubTypeGuid)

    def Encode(self):
        return pack("16s", self.SubTypeGuid)


class EFI_GUID_DEFINED_SECTION:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.SectionDefinitionGuid: bytes
        self.SectionDefinitionGuid_uuid: uuid.UUID
        self.DataOffset: int
        self.Attributes: int
        self.GuidSpecificHeaderFields: bytes
        self.Data: bytes
        self.Decode()

    def Decode(self):
        self.SectionDefinitionGuid = unpack("<16s", self.buff[:16])[0]
        self.SectionDefinitionGuid_uuid = uuid.UUID(
            bytes_le=self.SectionDefinitionGuid)
        self.DataOffset = unpack("<H", self.buff[16:18])[0]
        self.Attributes = unpack("<H", self.buff[18:20])[0]

    def Encode(self):
        return pack("<16sHH", self.SectionDefinitionGuid, self.DataOffset, self.Attributes)


class EFI_SECTION_USER_INTERFACE():
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.FileNameString: str

    def Decode(self):
        self.FileNameString = buff.decode('UTF-16-LE')

    def Encode(self):
        return self.FileNameString.encode('UTF-16-LE')


class EFI_SECTION_VERSION:
    def __init__(self, buff: bytes):
        self.buff: bytes = buff
        self.BuildNumber: int
        self.VersionString: str

    def decode(self):
        self.BuildNumber = unpack("<H", self.buff[:2])[0]
        self.VersionString = self.buff[2:].decode('UTF-16-LE')

    def encode(self):
        return pack("<H", self.BuildNumber) + self.VersionString.encode('UTF-16-LE')
