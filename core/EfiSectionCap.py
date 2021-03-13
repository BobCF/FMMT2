from core.EfiSectionBase import EfiSectionBase


class EfiSectionGuidDefined(EfiSectionBase):
    def __init__(self, sec_header, sec_buffer):
        super(EfiSectionGuidDefined, self).__init__(sec_header, sec_buffer)
        self.sec_ext_head = EFI_GUID_DEFINED_SECTION(
            buffer[sechead.common_head_size:sechead.common_head_size+20])

    def getSecData(self):
