# @file
#  Firmware Module Management Tool.
#
#  Copyright (c) 2021, Intel Corporation. All rights reserved.<BR>
#
#  SPDX-License-Identifier: BSD-2-Clause-Patent
#
##

# Import Modules
#
import argparse
import os
import io
import shutil
import logging
import sys
import tempfile

parser = argparse.ArgumentParser(description='''
SplitFile creates two Binary files either in the same directory as the current working directory or in the specified directory.
''')
parser.add_argument("-v", "--View", dest="InputFile",
                    help="View each FV and the named files within each FV.")
parser.add_argument("-d", "--split", dest="position",
                    help="The number of bytes in the first file. The valid format are HEX, Decimal and Decimal[KMG].")
parser.add_argument("-e", "--prefix",  dest="output",
                    help="The output folder.")
parser.add_argument("-a", "--firstfile",  help="The first file name")
parser.add_argument("--version", action="version", version='%(prog)s Version 1.0',
                    help="Print debug information.")

parser.add_argument("-r")

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


def main():
    args = parser.parse_args()
    status = 0

    logger = logging.getLogger('FMMT')
    logger.setLevel(logging.CRITICAL)

    lh = logging.StreamHandler(sys.stdout)
    lf = logging.Formatter("%(levelname)-8s: %(message)s")
    lh.setFormatter(lf)
    logger.addHandler(lh)

    try:
        fmmt = FMMT()
        fmmt.load("OVMF.fd")
        # TODO:
        '''Do the main work'''
    except Exception as e:
        print(e)

    return status


if __name__ == "__main__":
    exit(main())
