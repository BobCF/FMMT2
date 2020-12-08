from struct import unpack
class FV():
    def __init__(self,offset,ffs_guid,header):
        self.offset = offset 
        self.ffs_guid = ffs_guid
        self.header = header
    def __str__(self):
        return '''
        offset: %s \n
        ffs_guid: %s \n
        header: %s \n
        ''' % (self.offset,self.ffs_guid,self.header)
FvList = []
def displayLevel1Fv(fdfile):
    with open(fdfile,"rb") as fd:
        buffer = fd.read()
        for i in range(len(buffer) - 4):
            if buffer[i:i+4] == b'_FVH':
                header_len = int(unpack("=H",buffer[i+8:i+10])[0])
                guid = buffer[i-24:i-8] 
                FvList.append(FV(i-40,guid, str(header_len)))

if __name__ == "__main__":
    displayLevel1Fv(r"Ovmf.fd")
    for fv in FvList:
        print(fv)
