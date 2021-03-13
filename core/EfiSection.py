from core.EfiSectionLeaf import EfiSectionPe32
from core.EfiSectionLeaf import EfiSectionRaw
from core.EfiSectionCap import EfiSectionGuidDefined
EfiSections = {
    "EFI_SECTION_PE32": EfiSectionPe32,
    "EFI_SECTION_RAW": EfiSectionRaw,
    "EFI_SECTION_GUID_DEFINED": EfiSectionGuidDefined
}


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
