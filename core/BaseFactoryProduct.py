from PI.ExtendCType import *
from PI.Common import *
from core.NodeClass import *
from core.NodeTree import *
from core.GuidTools import *

ROOT_TREE = 'ROOT'
ROOT_FV_TREE = 'ROOT_FV_TREE'
ROOT_FFS_TREE = 'ROOT_FFS_TREE'
ROOT_SECTION_TREE = 'ROOT_SECTION_TREE'

FV_TREE = 'FV'
DATA_FV_TREE = 'DATA_FV'
FFS_TREE = 'FFS'
FFS_PAD = 'FFS_PAD'
FFS_FREE_SPACE = 'FFS_FREE_SPACE'
SECTION_TREE = 'SECTION'
SEC_FV_TREE = 'SEC_FV_IMAGE'
BINARY_DATA = 'BINARY'
Fv_count = 0

## Abstract factory
class BinaryFactory():
    type:list = []

    def Create_Product():
        pass

class BinaryProduct():
    ## Use GuidTool to decompress data.
    def DeCompressData(self, GuidTool, Section_Data):
        ParPath = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+os.path.sep+"..")
        ToolPath = os.path.join(ParPath, r'FMMTConfig.ini')
        print('struct2stream(GuidTool)', struct2stream(GuidTool))
        guidtool = GUIDTools(ToolPath).__getitem__(struct2stream(GuidTool))
        DecompressedData = guidtool.unpack(Section_Data)
        return DecompressedData

    def ParserData():
        pass
