import tempfile
from PI.FfsFileHeader import EFI_FFS_FILE_HEADER, EFI_FFS_FILE_HEADER2
from PI.FvHeader import EFI_FIRMWARE_VOLUME_HEADER
from PI.SectionHeader import *
import glob
import os
from dataclasses import dataclass
import io
from enum import Enum
import typing
import uuid
from struct import pack, unpack
from PI.FvHeader import *
from collections import OrderedDict

ZeroGuid = uuid.UUID('{00000000-0000-0000-0000-000000000000}')
EFI_FIRMWARE_CONTENTS_SIGNED_GUID = uuid.UUID(
    '{0f9d89e8-9259-4f76-a5af-0c89e34023df}')
EFI_FV_FILETYPE_FFS_PAD = 0xF0


def GET_OCCUPIED_SIZE(ActualSize, Alignment):
    return ((ActualSize) + (((Alignment) - ((ActualSize) & ((Alignment) - 1))) & ((Alignment) - 1)))


def CalculateCheckSum8(buffer, size):
    return 0x100 - CalculateSum8(buffer, size)


def CalculateSum8(buffer, size):
    Sum = 0
    for i in range(size):
        Sum = Sum + buffer[i]

    return Sum


class FW_STORAGE_TYPE(Enum):
    FV = 'FV'
    FFS = 'FFS'
    LSEC = 'LSEC'
    ESEC = 'ESEC'
    SEC = 'SEC'
    NA = 'NA'


class FwNode():
    def __init__(self, header=None, data=b''):
        self.id: uuid.UUID = uuid.uuid4()
        self.datatype: FW_STORAGE_TYPE = FW_STORAGE_TYPE.NA
        self.childlist: typing.List[FwNode] = []
        self.parent: FwNode = None
        self.header: object = header
        self.Data: bytes = data
        self.pad: bytes = b''

    def __str__(self):
        return str(self.id)


class FirmwarePacket():
    def __init__(self, buffer: bytes):
        self.buffer: bytes = buffer
        self.root: FwNode = FwNode()

    def insert(self, parentNode, newNode):
        parentNode.childlist.append(newNode)

    def update(self, parentNode, oldNode, newNode):
        all_exist_nodes = self.__search(parentNode, oldNode)
        for old_node in all_exist_nodes:
            subp = old_node.parent
            old_idx = subp.childlist.index(old_node)
            subp[old_idx] = newNode

    def delete(self, parentNode, oldNode):
        all_exist_nodes = self.__search(parentNode, oldNode)
        for old_node in all_exist_nodes:
            subp = old_node.parent
            if oldNode in subp.childlist:
                subp.childlist.remove(oldNode)

    def traverse(self):
        stack = [self.root]
        while stack:
            node = stack.pop()
            print(node)
            for child in node.childlist:
                stack.append(child)

    def search(self, fvid):
        pass

    def flush(self):
        pass

    def view(self):
        self.traverse()

    def getParent(self, node: FwNode) -> typing.List[FwNode]:
        parents = []
        stack = [self.root]
        while stack:
            n = stack.pop()
            if n == node:
                parents = n.parent
            for child in n.childlist:
                stack.append(child)
        return parents

    def getFv(self, scope: str) -> FwNode:
        return FwNode()

    def pack(self, outputfile) -> None:
        '''
        Pack the Firmware Storage Tree to a binary outputfile.
        '''
        pass

    def unpack(self):
        self.unpack_fv(self.root, self.buffer)

    def unpack_sec(self, parent, buffer):
        pass

    def unpack_fv(self, parent, buffer):
        '''
        Unpack the binary into Firmware Storage Tree.
        '''
        Fv = FirmwareVolume()
        for fvhead, fvdata in Fv.discover(buffer):
            fv_node = FwNode(fvhead, fvdata)
            self.insert(parent, fv_node)
            Ffshandler = FirmwareFile(fv_node)
            for ffshead, ffsdata in Ffshandler.discover(fvdata):
                ffs_node = FwNode(ffshead, ffsdata)
                self.insert(fv_node, ffs_node)
                if ffshead.Type == EFI_FV_FILETYPE_FFS_PAD:
                    continue
                SecHandler = FirmwareSection()
                for sechead, secdata in SecHandler.discorver(ffsdata):
                    sec_node = FwNode(sechead, secdata)
                    self.insert(ffs_node, sec_node)
                    if sechead.Type == "COMPRESS":
                        sec_list = uncompress(sec_node)
                        for sec in sec_list:
                            self.unpack_sec(sec_node, sec)
                    elif sechead.Type == "GUID":
                        sec_list = unguid(sec_node)
                        for sec in sec_list:
                            self.unpack_sec(sec_node, sec)
                    elif sechead.Type == "FV":
                        self.unpack_fv(sec_node, secdata)


class Decoder():
    def process(self, buffer: bytes):
        raise NotImplementedError


class Encoder():
    def process(self, node: FwNode):
        raise NotImplementedError


class FVEncoder(Encoder):
    def process(self, node: FwNode):
        print("FvEncoder")


class FVDecoder(Decoder):
    def process(self, buffer: bytes):
        fv_header = EFI_FIRMWARE_VOLUME_HEADER(buffer)
        return fv_header, buffer[fv_header.HeaderLength:fv_header.FvLength]


class FFSEncoder(Encoder):
    def process(self, node: FwNode):
        print("FFSEncoder prcess")


class FFSDecoder(Decoder):
    def process(self, buffer: bytes):
        pass


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
    EFI_FVB2_ERASE_POLARITY = 0x00000800
    FFS_FIXED_CHECKSUM = 0xAA
    FFS_ATTRIB_CHECKSUM = 0x40
    FFS_ATTRIB_LARGE_FILE = 0x01
    EFI_FILE_HEADER_CONSTRUCTION = 0x01
    EFI_FILE_HEADER_VALID = 0x02
    EFI_FILE_DATA_VALID = 0x04
    EFI_FILE_MARKED_FOR_UPDATE = 0x08
    FI_FILE_DELETED = 0x10
    EFI_FILE_HEADER_INVALID = 0x20
    FFS_FILE_STATE = [
        EFI_FILE_HEADER_CONSTRUCTION,
        EFI_FILE_HEADER_VALID,
        EFI_FILE_DATA_VALID,
        EFI_FILE_MARKED_FOR_UPDATE,
        FI_FILE_DELETED,
        EFI_FILE_HEADER_INVALID
    ]

    def __init__(self, parent_fv):
        super(FirmwareFile, self).__init__()
        self.parent_fv = parent_fv

    def is_ffs_file2(self, ffsheader):
        return (ffsheader.Attributes & self.FFS_ATTRIB_LARGE_FILE) == self.FFS_ATTRIB_LARGE_FILE

    def VerifyFwFile(self, ffsheader, ffsdata):
        FvAttr = self.parent_fv.header.Attributes
        if FvAttr & self.EFI_FVB2_ERASE_POLARITY:
            ffs_state = 0xff - ffsheader.State
        else:
            ffs_state = ffsheader.State

        #
        # Get file state set by its highest none zero bit.
        #
        HighestBit = 0x80
        while (HighestBit != 0 and (HighestBit & ffs_state) == 0):
            HighestBit >>= 1

        if HighestBit not in self.FFS_FILE_STATE:
            return False

        DataCheckSum = self.FFS_FIXED_CHECKSUM

        if ffsheader.Attributes & self.FFS_ATTRIB_CHECKSUM == self.FFS_ATTRIB_CHECKSUM:
            if self.is_ffs_file2(ffsheader):
                DataCheckSum = CalculateCheckSum8(
                    ffsdata, ffsheader.FFS_FILE_SIZE - 32)
            else:
                DataCheckSum = CalculateCheckSum8(
                    ffsdata, ffsheader.FFS_FILE_SIZE - 24)
        if ffsheader.IntegrityCheck.Checksum.File != DataCheckSum:
            return False
        return True

    def discover(self, buffer: bytes) -> list:
        ffs_list = []
        i = 0
        while i < len(buffer):
            ffs_head = EFI_FFS_FILE_HEADER(buffer[i:])
            ffs_head_size = 24
            if self.is_ffs_file2(ffs_head):
                ffs_head = EFI_FFS_FILE_HEADER2(buffer[i:])
                ffs_head_size = 32
            ffs_data = buffer[i+ffs_head_size:i+ffs_head.FFS_FILE_SIZE]
            if not self.VerifyFwFile(ffs_head, ffs_data):
                break
            ffs_list.append((ffs_head, ffs_data))
            i = i + GET_OCCUPIED_SIZE(ffs_head.FFS_FILE_SIZE, 8)
            print(ffs_head.Name_uuid)
        return ffs_list


class FirmwareVolume(FirmwareStorage):

    def decode(self, buffer: bytes) -> tuple:
        decoder = firmware_handler_factory.get_decoder(FW_STORAGE_TYPE.FV)
        fvheader, fvdata = decoder.process(buffer)
        return fvheader, fvdata

    def encode(self, fwnode: FwNode):
        encoder = firmware_handler_factory.get_encoder(FW_STORAGE_TYPE.FV)
        buffer = encoder.process()
        return buffer

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
                    buffer[FvStart:])
                assert(fvheader.ZeroVector == ZeroGuid.bytes)
                if fvheader.ExtHeader:
                    print(fvheader.ExtHeader.FvName_uuid)
                else:
                    print(fvheader.FileSystemGuid_uuid)
                assert (fvheader.Encode() == buffer[FvStart:FvStart+FvHSize])
                FvList.append(
                    (fvheader, buffer[FvStart+FvHSize:FvStart+fvheader.FvLength]))
                i += fvheader.FvLength
                continue
            i += 1
        return FvList


class FirmwareSection(FirmwareStorage):

    # ************************************************************
    # The section type EFI_SECTION_ALL is a pseudo type. It is
    # used as a wild card when retrieving sections. The section
    # type EFI_SECTION_ALL matches all section types.
    # ************************************************************
    EFI_SECTION_ALL = 0x00
    # ************************************************************
    # Encapsulation section Type values
    # ************************************************************
    EFI_SECTION_COMPRESSION = 0x01
    EFI_SECTION_GUID_DEFINED = 0x02
    EFI_SECTION_DISPOSABLE = 0x03
    # ************************************************************
    # Leaf section Type values
    # ************************************************************
    EFI_SECTION_PE32 = 0x10
    EFI_SECTION_PIC = 0x11
    EFI_SECTION_TE = 0x12
    EFI_SECTION_DXE_DEPEX = 0x13
    EFI_SECTION_VERSION = 0x14
    EFI_SECTION_USER_INTERFACE = 0x15
    EFI_SECTION_COMPATIBILITY16 = 0x16
    EFI_SECTION_FIRMWARE_VOLUME_IMAGE = 0x17
    EFI_SECTION_FREEFORM_SUBTYPE_GUID = 0x18
    EFI_SECTION_RAW = 0x19
    EFI_SECTION_PEI_DEPEX = 0x1B
    EFI_SECTION_MM_DEPEX = 0x1C

    def decode(self, buffer: bytes) -> tuple:
        decoder = firmware_handler_factory.get_decoder(FW_STORAGE_TYPE.SEC)
        secheader, secdata = decoder.process()
        return secheader, secdata

    def encode(self):
        encoder = firmware_handler_factory.get_encoder(FW_STORAGE_TYPE.SEC)
        buffer = encoder.process()
        return buffer

    def discorver(self, buffer: bytes) -> list:
        SecList = []
        i = 0
        while i < len(buffer):
            sechead = EFI_COMMON_SECTION_HEADER(buffer)
            if sechead.SECTION_SIZE == 0xFFFFFF:
                sechead = EFI_COMMON_SECTION_HEADER2(buffer)
            if sechead.Type == self.EFI_SECTION_COMPRESSION:
                print("EFI_COMMON_SECTION_COMPRESSION")
            elif sechead.Type == self.EFI_SECTION_GUID_DEFINED:
                sec_ext_head = EFI_GUID_DEFINED_SECTION(
                    buffer[sechead.common_head_size:sechead.common_head_size+20])
                guidtool = guidtools[sec_ext_head.SectionDefinitionGuid_uuid]
                sechead.ExtHeader = sec_ext_head
                SecList.append((sechead,
                                guidtool.unpack(buffer[sechead.common_head_size+20:sechead.SECTION_SIZE])))
                print("EFI_SECTION_GUID_DEFINED")
            elif sechead.Type == self.EFI_SECTION_DISPOSABLE:
                print("EFI_SECTION_DISPOSABLE")
                pass
            elif sechead.Type == self.EFI_SECTION_PE32:
                print("EFI_SECTION_PE32")
                pass
            elif sechead.Type == self.EFI_SECTION_PIC:
                print("EFI_SECTION_PIC")
                pass
            elif sechead.Type == self.EFI_SECTION_TE:
                print("EFI_SECTION_TE")
                pass
            elif sechead.Type == self.EFI_SECTION_DXE_DEPEX:
                print("EFI_SECTION_DXE_DEPEX")
                pass
            elif sechead.Type == self.EFI_SECTION_VERSION:
                print("EFI_SECTION_VERSION")
                sec_ext_head = EFI_SECTION_VERSION(
                    buffer[sechead.common_head_size:sechead.common_head_size+sechead.SECTION_SIZE])
                sechead.ExtHeader = sec_ext_head
                print(sec_ext_head.VersionString)
                SecList.append(sechead, b'')
            elif sechead.Type == self.EFI_SECTION_USER_INTERFACE:
                print("EFI_SECTION_USER_INTERFACE")
                sec_ext_head = EFI_SECTION_USER_INTERFACE(
                    buffer[sechead.common_head_size:sechead.common_head_size+sechead.SECTION_SIZE])
                sechead.ExtHeader = sec_ext_head
                print(sec_ext_head.FileNameString)
                SecList.append(sechead, b'')
                pass
            elif sechead.Type == self.EFI_SECTION_COMPATIBILITY16:
                print("EFI_SECTION_USER_COMPATIBILITY16")
                pass
            elif sechead.Type == self.EFI_SECTION_FIRMWARE_VOLUME_IMAGE:
                print("EFI_SECTION_USER_FIRMWARE_VOLUME_IMAGE")
                pass
            elif sechead.Type == self.EFI_SECTION_FREEFORM_SUBTYPE_GUID:
                print("EFI_SECTION_FREEFORM_SUBTYPE_GUID")
                pass
            elif sechead.Type == self.EFI_SECTION_RAW:
                print("EFI_SECTION_RAW", sechead.SECTION_SIZE)
                pass
            elif sechead.Type == self.EFI_SECTION_PEI_DEPEX:
                print("EFI_SECTION_PEI_DEPEX")
                pass
            elif sechead.Type == self.EFI_SECTION_MM_DEPEX:
                print("EFI_SECTION_MM_DEPEX")
                pass
            else:
                print("EFI_COMMON_SEC")

            i += sechead.SECTION_SIZE
        return SecList


firmware_storage_factory.register(FW_STORAGE_TYPE.FV, FirmwareVolume)
firmware_storage_factory.register(FW_STORAGE_TYPE.LSEC, FirmwareFile)


def ExtractBytool(toolguid: uuid.UUID, buff: bytes) -> bytes:
    tool = guidtools[toolguid]
    tempd = tempfile.mkdtemp()
    secfile = os.path.join(tempd, "sec.bin")
    uncompressed_secfile = os.path.join(tempd, "uncom_sec.bin")
    with open(secfile, "wb") as fd:
        fd.write(buff)
    tool.unpack(input=secfile, output=uncompressed_secfile)
    with open(uncompressed_secfile, "rd") as fd:
        uncomp_bin = fd.read()

    return uncomp_bin


class GUIDTool:
    def __init__(self, guid, short_name, command):
        self.guid: str = guid
        self.short_name: str = short_name
        self.command: str = command

    def pack(self, *args, **kwargs):
        pass

    def unpack(self, *args, **kwargs):
        pass


class TianoCompress(GUIDTool):
    def pack(self, *args, **kwargs):
        pass

    def unpack(self, *args, **kwargs):
        pass


class TianoCompress(GUIDTool):
    def pack(self, *args, **kwargs):
        pass

    def unpack(self, *args, **kwargs):
        pass


class LzmaCompress(GUIDTool):
    def pack(self, *args, **kwargs):
        pass

    def unpack(self, *args, **kwargs):
        pass


class GenCrc32(GUIDTool):
    def pack(self, *args, **kwargs):
        pass

    def unpack(self, *args, **kwargs):
        pass


class LzmaF86Compress(GUIDTool):
    def pack(self, *args, **kwargs):
        pass

    def unpack(self, *args, **kwargs):
        pass


class BrotliCompress(GUIDTool):
    def pack(self, *args, **kwargs):
        pass

    def unpack(self, *args, **kwargs):
        pass


class GUIDTools:
    '''
    GUIDTools is responsible for reading FMMTConfig.ini, verify the tools and provide interfaces to access those tools.
    '''
    default_tools = {
        uuid.UUID("{a31280ad-481e-41b6-95e8-127f4c984779}"): TianoCompress("a31280ad-481e-41b6-95e8-127f4c984779", "TIANO", "TianoCompress"),
        uuid.UUID("{ee4e5898-3914-4259-9d6e-dc7bd79403cf}"): LzmaCompress("ee4e5898-3914-4259-9d6e-dc7bd79403cf", "LZMA", "LzmaCompres"),
        uuid.UUID("{fc1bcdb0-7d31-49aa-936a-a4600d9dd083}"): GenCrc32("fc1bcdb0-7d31-49aa-936a-a4600d9dd083", "CRC32", "GenCrc32"),
        uuid.UUID("{d42ae6bd-1352-4bfb-909a-ca72a6eae889}"): LzmaF86Compress("d42ae6bd-1352-4bfb-909a-ca72a6eae889", "LZMAF86", "LzmaF86Compress"),
        uuid.UUID("{3d532050-5cda-4fd0-879e-0f7f630d5afb}"): BrotliCompress("3d532050-5cda-4fd0-879e-0f7f630d5afb", "BROTLI", "BrotliCompress")
    }

    def __init__(self, tooldef_file=None):
        selfdir = os.path.dirname(__file__)
        self.tooldef_file = tooldef_file if tooldef_file else os.path.join(
            selfdir, "FMMTConfig.ini")
        self.tooldef = dict()
        self.load()

    def VerifyTools(self):
        path_env = os.environ.get("PATH")
        path_env_list = path_env.split(os.pathsep)
        path_env_list.append(os.path.dirname(__file__))
        path_env_list = list(set(path_env_list))
        for tool in self.tooldef.values():
            cmd = tool.command
            if os.path.isabs(cmd):
                if not os.path.exists(cmd):
                    print("Tool Not found %s" % cmd)
            else:
                for syspath in path_env_list:
                    if glob.glob(os.path.join(syspath, cmd+"*")):
                        break
                else:
                    print("Tool Not found %s" % cmd)

    def load(self):
        if os.path.exists(self.tooldef_file):
            with open(self.tooldef_file, "r") as fd:
                config_data = fd.readlines()
            for line in config_data:
                try:
                    guid, short_name, command = line.split()
                    self.tooldef[uuid.UUID(guid.strip())] = GUIDTool(
                        guid.strip(), short_name.strip(), command.strip())
                except:
                    print("error")
                    continue
        else:
            self.tooldef.update(self.default_tools)

        self.VerifyTools()

    def __getitem__(self, guid):
        return self.tooldef.get(guid)


guidtools = GUIDTools()


class FMMT():
    def __init__(self):
        self.firmware_packet = None

    def load(self, fv_file):
        with open(fv_file, "rb") as fd:
            buffer = fd.read()
        self.firmware_packet = FirmwarePacket(buffer)
        self.firmware_packet.unpack()

    def insert(self, fvid, ffspath):
        fv_node = self.firmware_packet.search(fvid)
        Ffs_handler = FirmwareFile(fv_node)
        with open(ffspath, 'rb') as fd:
            ffsbuffer = fd.read()
        ffs_node = FwNode(Ffs_handler.decode(ffsbuffer))
        self.firmware_packet.insert(fv_node, ffs_node)
        self.firmware_packet.flush()

    def delete(self, fvid, ffsname):
        fv_node = self.firmware_packet.search(fvid)
        self.firmware_packet.delete(fv_node, ffsname)
        self.firmware_packet.flush()

    def update(self, fvid, oldffsname, newffspath):
        fv_node = self.firmware_packet.search(fvid)
        with open(newffspath, 'rb') as fd:
            ffsbuffer = fd.read()
        Ffs_handler = FirmwareFile(fv_node)
        ffs_node = FwNode(Ffs_handler.decode(ffsbuffer))
        self.firmware_packet.update(fv_node, oldffsname, ffs_node)
        self.firmware_packet.flush()

    def view(self):
        self.firmware_packet.view()


if __name__ == "__main__":
    fmmt = FMMT()
    fmmt.load("OVMF.fd")
