from struct import *
import uuid


class EFI_FFS_INTEGRITY_CHECK:
    def __init__(self, buffer: bytes):
        self.buffer: bytes = buffer
        self.Header: int
        self.File: int
        self.Checksum16: int

    def Decode(self, buffer: bytes):
        pass

    def Encode(self) -> bytes:
        pass


class EFI_FFS_INTEGRITY_CHECK():
    class _Checksum():
        def __init__(self):
            self.Header: int
            self.File: int

    def __init__(self, buffer: bytes):
        self.Checksum = self._Checksum()
        self.Checksum.Header = buffer[0]
        self.Checksum.File = buffer[1]
        self.Checksum16: int = buffer


class EFI_FFS_FILE_HEADER:
    def __init__(self, buffer: bytes):
        self.buffer = buffer
        self.Name: bytes
        self.IntegrityCheck: bytes
        self.Type: int
        self.Attributes: int
        self.Size: list
        self.State: int
        self.Decode(buffer)
        self.Name_uuid = uuid.UUID(bytes_le=self.Name)

    def Decode(self, buffer):
        self.Name = unpack("<16s", buffer[:16])[0]
        self.IntegrityCheck = EFI_FFS_INTEGRITY_CHECK(buffer[16:18])
        (self.Type, self.Attributes) = unpack("<BB", buffer[18:20])
        self.Size = unpack("<BBB", buffer[20:23])
        self.State = unpack("<B", buffer[23:24])[0]

    @property
    def FFS_FILE_SIZE(self):
        return self.Size[0] | self.Size[1] << 8 | self.Size[2] << 16

    def Encode(self) -> bytes:
        buff = b''
        buff += pack("<16s", self.Name)
        buff += self.IntegrityCheck
        buff += pack("<BB", self.Type, self.Attributes)
        buff += pack("<BBB", self.Size[0], self.Size[1].self.Size[2])
        buff += pack("<B", self.State)


class EFI_FFS_FILE_HEADER2:
    def __init__(self, buffer: bytes):
        self.buffer = buffer
        self.Name: bytes
        self.IntegrityCheck: bytes
        self.Type: int
        self.Attributes: int
        self.Size: list
        self.State: int
        self.ExtendedSize: int
        self.Decode(buffer)
        self.Name_uuid = uuid.UUID(bytes_le=self.Name)

    def Decode(self, buffer):
        self.Name = unpack("<16s", buffer[:16])[0]
        self.IntegrityCheck = buffer[16:18]
        (self.Type, self.Attributes) = unpack("<BB", buffer[18:20])
        self.Size = unpack("<BBB", buffer[20:23])
        self.State = unpack("<B", buffer[23:24])[0]
        self.ExtendedSize = unpack("<Q", buffer[24:32])[0]

    @property
    def FFS_FILE_SIZE(self):
        return self.ExtendedSize

    def Encode(self) -> bytes:
        buff = b''
        buff += pack("<16s", self.Name)
        buff += self.IntegrityCheck
        buff += pack("<BB", self.Type, self.Attributes)
        buff += pack("<BBB", self.Size[0], self.Size[1].self.Size[2])
        buff += pack("<B", self.State)
        buff += pack("<Q", self.ExtendedSize)
