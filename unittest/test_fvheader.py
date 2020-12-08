import pytest
import uuid
from DataStruct.FvHeader import *

FvBuffers = [r"unittest\Ovmf.fd", r"unittest\PEIFV.fv"]

zeroguid = uuid.UUID('{00000000-0000-0000-0000-000000000000}')


class TestFvHeader():
    @pytest.fixture(params=FvBuffers)
    def case(self, request):
        fv_file = request.param
        with open(fv_file, "rb") as fd:
            buffer = fd.read()
        yield buffer

    def test_fvheader(self, case):
        buffer = case
        FvStart = 0
        FvHSize = 0
        i = 0
        while i < len(buffer):
            if buffer[i:i+4] == b'_FVH' and buffer[i-40:i-40+16] == zeroguid.bytes:
                FvStart = i - 40
                FvHSize = unpack("<H", buffer[i+8:i+10])[0]
                fvheader = EFI_FIRMWARE_VOLUME_HEADER(
                    buffer[FvStart:FvStart+FvHSize])
                assert(fvheader.ZeroVector == zeroguid.bytes)
                print(fvheader.ExtHeaderOffset)
                assert (fvheader.Encode() == buffer[FvStart:FvStart+FvHSize])
                i += fvheader.FvLength
                continue
            i += 1
