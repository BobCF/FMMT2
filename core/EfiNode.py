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


firmware_storage_factory = FirwmareStorageFactory(

class FW_STORAGE_TYPE(Enum):
    FV='FV'
    FFS='FFS'
    LSEC='LSEC'
    ESEC='ESEC'
    SEC='SEC'
    NA='NA'


class FwNode():
    def __init__(self, header=None, data=b''):
        self.id: uuid.UUID=uuid.uuid4()
        self.offset: int=0
        self.size: int=0
        self.datatype: FW_STORAGE_TYPE=FW_STORAGE_TYPE.NA
        self.childlist: typing.List[FwNode]=[]
        self.parent: FwNode=None
        self.header: object=header
        self.Data: bytes=data
        self.pad: bytes=b''

    def __str__(self):
        return str(self.id)


class FirmwareDevice():
    def __init__(self, buffer: bytes):
        self.buffer: bytes=buffer
        self.root: FwNode=FwNode()

    def insert(self, parentNode, newNode):
        parentNode.childlist.append(newNode)

    def update(self, parentNode, oldNode, newNode):
        all_exist_nodes=self.__search(parentNode, oldNode)
        for old_node in all_exist_nodes:
            subp=old_node.parent
            old_idx=subp.childlist.index(old_node)
            subp[old_idx]=newNode

    def delete(self, parentNode, oldNode):
        all_exist_nodes=self.__search(parentNode, oldNode)
        for old_node in all_exist_nodes:
            subp=old_node.parent
            if oldNode in subp.childlist:
                subp.childlist.remove(oldNode)

    def traverse(self):
        stack=[self.root]
        while stack:
            node=stack.pop()
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
        parents=[]
        stack=[self.root]
        while stack:
            n=stack.pop()
            if n == node:
                parents=n.parent
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
        Fv=FirmwareVolume()
        for fvhead, fvdata in Fv.discover(buffer):
            fv_node=FwNode(fvhead, fvdata)
            self.insert(parent, fv_node)
            Ffshandler=FirmwareFile(fv_node)
            for ffshead, ffsdata in Ffshandler.discover(fvdata):
                ffs_node=FwNode(ffshead, ffsdata)
                self.insert(fv_node, ffs_node)
                if ffshead.Type == EFI_FV_FILETYPE_FFS_PAD:
                    continue
                SecHandler=FirmwareSection()
                for sechead, secdata in SecHandler.discorver(ffsdata):
                    sec_node=FwNode(sechead, secdata)
                    self.insert(ffs_node, sec_node)
                    if sechead.Type == "COMPRESS":
                        sec_list=uncompress(sec_node)
                        for sec in sec_list:
                            self.unpack_sec(sec_node, sec)
                    elif sechead.Type == "GUID":
                        sec_list=unguid(sec_node)
                        for sec in sec_list:
                            self.unpack_sec(sec_node, sec)
                    elif sechead.Type == "FV":
                        self.unpack_fv(sec_node, secdata)
