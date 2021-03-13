form core.EfiSectionBase import EfiSectionBase


class EfiSectionPe32(EfiSectionBase):
    def __init__(self, sec_header, sec_buffer):
        super(EfiSectionPe32, self).__init__(sec_header, sec_buffer)


class EfiSectionRaw(EfiSectionBase):
    def __init__(self, sec_header, sec_buffer):
        super(EfiSectionRaw, self).__init__(sec_header, sec_buffer)
