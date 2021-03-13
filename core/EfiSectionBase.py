class EfiSectionBase():
    def __init__(self, sec_header, sec_buffer):
        self.sec_header = sec_header
        self.sec_buffer = sec_buffer
        self.ext_header = None

    def getSecData():
        raise NotImplemented
