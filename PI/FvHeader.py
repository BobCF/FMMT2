from struct import *
import uuid


class EFI_FIRMWARE_VOLUME_HEADER:
    def __init__(self, buffer: bytes):
        self.buffer: bytes = buffer
        self.ZeroVector: str
        self.FileSystemGuid: str
        self.FvLength: int = 0
        self.Signature: int = 0
        self.Attributes: int = 0
        self.HeaderLength: int = 0
        self.Checksum: int = 0
        self.ExtHeaderOffset: int = 0
        self.Reserved: int = 0
        self.Revision: int = 0
        self.BlockMap: list = []
        self.FixedFieldFormat: str = "<16s16sQ4sLHHHBB"
        self.Decode()
        if self.ExtHeaderOffset:
            self.ExtHeader = EFI_FIRMWARE_VOLUME_EXT_HEADER(
                buffer[self.ExtHeaderOffset:])
            self.ExtHeader.Decode()
        else:
            self.ExtHeader = None

    def Decode(self):
        self.AllFieldFormat = self.FixedFieldFormat
        (
            self.ZeroVector,
            self.FileSystemGuid,
            self.FvLength,
            self.Signature,
            self.Attributes,
            self.HeaderLength,
            self.Checksum,
            self.ExtHeaderOffset,
            self.Reserved,
            self.Revision
        ) = unpack(self.FixedFieldFormat, self.buffer[:56])
        for i in range((self.HeaderLength - 56)//8):
            self.BlockMap.append(unpack("<2L", self.buffer[56+i*8:56+(i+1)*8]))
        self.FileSystemGuid_uuid = uuid.UUID(bytes_le=self.FileSystemGuid)
        return self

    def Encode(self) -> bytes:
        buffer = pack(self.FixedFieldFormat,
                      self.ZeroVector,
                      self.FileSystemGuid,
                      self.FvLength,
                      self.Signature,
                      self.Attributes,
                      self.HeaderLength,
                      self.Checksum,
                      self.ExtHeaderOffset,
                      self.Reserved,
                      self.Revision
                      )
        for block in self.BlockMap:
            buffer += pack("<2L", block[0], block[1])
        return buffer


class EFI_FIRMWARE_VOLUME_EXT_HEADER:
    def __init__(self, buffer: bytes):
        self.buffer: bytes = buffer
        self.FvName: bytes = b''
        self.ExtHeaderSize: int = 0

    def Decode(self):
        self.FvName, self.ExtHeaderSize = unpack(
            "<16sL", self.buffer[:20]
        )
        self.FvName_uuid = uuid.UUID(bytes_le=self.FvName)

    def Encode(self) -> bytes:
        return pack("<16sL", self.FvName, self.ExtHeaderSize)
