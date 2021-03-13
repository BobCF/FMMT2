import uuid

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