import io
from enum import Enum
import typing
import uuid


class FW_STORAGE_TYPE(Enum):
    FV = 'FV'
    FFS = 'FFS'
    LSEC = 'LSEC'
    ESEC = 'ESEC'
    SEC = 'SEC'
    NA = 'NA'


class FwNode():
    def __init__(self):
        self.id: uuid.UUID = uuid.uuid4()
        self.datatype: FW_STORAGE_TYPE = FW_STORAGE_TYPE.NA
        self.childlist: typing.List[FwNode] = []
        self.parent: FwNode = None
        self.header: object = None
        self.Data: bytes = b''
        self.pad: bytes = b''

    def __str__(self):
        return str(self.id)


class FirmwarePacket():
    def __init__(self, buffer: bytes):
        self.buffer: bytes = buffer
        self.root: FwNode = FwNode()

    def insert(self, newNode, scope=None):
        FvNode = self.getFv(scope)
        FvNode.childlist.append(newNode)

    def update(self, oldNode, newNode, scope=None):
        parentNodes = self.getParenet(oldNode)
        if scope:
            parentNode = [item for item in parentNodes if item.id == scope]
        for p in parentNode:
            if oldNode in parentNode.childlist:
                old_idx = parenetNode.childlist.index(oldNode)
                parenetNode[old_idx] = newNode
            else:
                parenetNode.childlist.append(newNode)

    def delete(self, oldNode, scope=None):
        parentNodes = self.getParent(oldNode)
        if scope:
            parentNodes = [item for item in parentNodes if item.id == scope]
        for p in parentNodes:
            if oldNode in parentNode.childlist:
                parentNode.childlist.remove(oldNode)

    def traverse(self):
        stack = [self.root]
        while stack:
            node = stack.pop()
            print(node)
            for child in node.childlist:
                stack.append(child)

    def getParent(self, node: FwNode) -> typing.List[FwNode]:
        parents = []
        statck = [self.root]
        while stack:
            n = stack.pop()
            if n == node:
                parents = n.parent
            for child in n.childlist:
                stack.append(child)
        return parents

    def getFv(self, scope: str) -> FwNode:
        return FwNode()


class Decoder():
    def process(self, buffer: bytes):
        raise NotImplementedError


class Encoder():
    def process(self, node: FwNode):
        raise NotImplementedError


class FDDecoder(Decoder):
    def process(self, buffer: bytes):
        print("FDDecoder prcess")


class FVEncoder(Encoder):
    def process(self, node: FwNode):
        print("FVEncoder prcess")


class FVDecoder(Decoder):
    def process(self, buffer: bytes):
        print("FVDecoder prcess")


class FFSEncoder(Encoder):
    def process(self, node: FwNode):
        print("FFSEncoder prcess")


class FFSDecoder(Decoder):
    def process(self, buffer: bytes):
        print("FFSDecoder prcess")


class SECEncoder(Encoder):
    def process(self, node: FwNode):
        print("SecEncoder prcess")


class SECDecoder(Decoder):
    def process(self, buffer: bytes):
        print("SecDecoder prcess")


class FirwmareStorageHandlerFactory():
    def __init__(self):
        self.decoders = {}
        self.encoders = {}

    def register_encoder(self, fwstype: FW_STORAGE_TYPE, encoder: typing.Type[Encoder]):
        self.encoders[fwstype] = encoder

    def register_decoder(self, fwstype: FW_STORAGE_TYPE, decoder: typing.Type[Decoder]):
        self.decoders[fwstype] = decoder

    def get_encoder(self, fwtype):
        encoder = self.encoders.get(fwtype)
        if encoder is None:
            raise ValueError(fwtype)
        return encoder()

    def get_decoder(self, fwtype):
        decoder = self.decoders.get(fwtype)
        if decoder is None:
            raise ValueError(fwtype)
        return decoder()


firmware_handler_factory = FirwmareStorageHandlerFactory()

firmware_handler_factory.register_encoder(FW_STORAGE_TYPE.FV, FVEncoder)
firmware_handler_factory.register_decoder(FW_STORAGE_TYPE.FV, FVDecoder)
firmware_handler_factory.register_encoder(FW_STORAGE_TYPE.FFS, FFSEncoder)
firmware_handler_factory.register_decoder(FW_STORAGE_TYPE.FFS, FFSDecoder)
firmware_handler_factory.register_encoder(FW_STORAGE_TYPE.LSEC, SECEncoder)
firmware_handler_factory.register_decoder(FW_STORAGE_TYPE.LSEC, SECDecoder)


class FirmwareStorage():
    def encode(self, fwnode: FwNode):
        raise NotImplementedError

    def decode(self, parent: FwNode, buffer: bytes):
        raise NotImplementedError


class FirwmareStorageFactory():
    def __init__(self):
        self.storages = {}

    def register(self, fwstype: FW_STORAGE_TYPE, s: typing.Type[FirmwareStorage]):
        self.storages[fwstype] = s

    def get_storage(self, fwtype: FW_STORAGE_TYPE):
        s = self.storages.get(fwtype)
        if s is None:
            raise ValueError(fwtype)
        return s()


firmware_storage_factory = FirwmareStorageFactory()


class FirmwareFile(FirmwareStorage):

    def decode(self, parent: FwNode, buffer: bytes):
        print("FFS process_decoding")
        ffslist = self.discover(buffer)
        for ffs in ffslist:
            ffsheader, ffsdata = self.parse(ffs)
            lower_layer = firmware_storage_factory.get_storage(
                FW_STORAGE_TYPE.LSEC)
            ffsnode = FwNode()
            lower_layer.decode(ffsnode, ffsdata)
            parent.childlist.append(ffsnode)

    def encode(self, fwnode: FwNode):
        print("FFS process_encoding")

    def discover(self, buffer: bytes) -> list:
        return []

    def parse(self, buffer: bytes) -> tuple:
        header, data = b'', b''
        return header, data


class FirmwareVolume(FirmwareStorage):

    def decode(self, parent: FwNode, buffer: bytes):
        print("Fv process_decoding")
        fvlist = self.discover(buffer)
        for fv in fvlist:
            fvheader, fvdata = self.parse(fv)
            lower_layer = firmware_storage_factory.get_storage(
                FW_STORAGE_TYPE.FFS)
            fvnode = FwNode()
            lower_layer.decode(fvnode, fvdata)
            parent.childlist.append(fvnode)

    def encode(self, fwnode: FwNode):
        print("Fv process_encoding")

    def discover(self, buffer: bytes) -> list:
        FvList = []
        FvStart = 0
        FvHSize = 0
        i = 0
        while i < len(buffer):
            if buffer[i:i+4] == b'_FVH' and buffer[i-40:i-40+16] == ZeroGuid.bytes:
                FvStart = i - 40
                FvHSize = unpack("<H", buffer[i+8:i+10])[0]
                fvheader = EFI_FIRMWARE_VOLUME_HEADER(
                    buffer[FvStart:FvStart+FvHSize])
                assert(fvheader.ZeroVector == ZeroGuid.bytes)
                print(fvheader.ExtHeaderOffset)
                assert (fvheader.Encode() == buffer[FvStart:FvStart+FvHSize])
                FvList.append((FvStart, fvheader.FvLength))
                i += fvheader.FvLength
                continue
            i += 1

    def parse(self, buffer: bytes) -> tuple:
        fvheader = b''
        fvdata = b''
        decoder = firmware_handler_factory.get_decoder(FW_STORAGE_TYPE.FV)
        fvheader, fvdata = decoder.process()
        return fvheader, fvdata


firmware_storage_factory.register(FW_STORAGE_TYPE.FV, FirmwareVolume)
firmware_storage_factory.register(FW_STORAGE_TYPE.LSEC, FirmwareFile)

if __name__ == "__main__":
    buffer = io.BytesIO(b"test").read()
    f_packet = FirmwarePacket(buffer)
    Fv = FirmwareVolume()
    Fv.decode(f_packet.root, f_packet.buffer)
