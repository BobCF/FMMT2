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
import glob
import os
import io
import shutil
import logging
import sys
import tempfile

parser = argparse.ArgumentParser(prog="FMMT", description='''Firmware Module Management Tool''',
                                 epilog='''
Note: 
1. <FV-id> is the sequence of the firmware volume included in the FD image, it both support the 
sequentially format like FV0, FV1 and the FV's file guid value format.
2. <-d> args format: <input-binary-file> <FV-id> <output-binary-file> or  
<input-binary-file> <FV-id> <File-Name|File-Guid> [<FV-id> <File-Name|File-Guid> ...] <output-binary-file>.
3. <-e> args format:  <input-binary-file> <FV-id> <File-Name> [<FV-id> <File-Name> ...] \
                                            <output-binary-file|output-directory>.
4. <-a> args format: <input-binary-file> <FV-id> <NewFilePath> [<FV-id> <NewFilePath> ...] <output-binary-file>.
5. <-r> args format: <input-binary-file> <FV-id> <File-Name|File-Guid> <NewFilePath> [<FV-id> <File-Name|File-Guid> \
<NewFilePath> ...] <output-binary-file>.
''')

parser.add_argument('-v', '--view', help="View each FV and the named files within each FV.")
parser.add_argument('-d', '--delete', nargs="+", help="Delete entire FV in an FD file(Delete a file (or files) from \
                                                      the firmware volume in an FD binary)")
# parser.add_argument('-e', '--extract', nargs='+', help="Delete a file (or files) from the firmware volume \
#                                                       in an FD binary")
parser.add_argument('-a', '--add', nargs='+', help="Add a file (or files) to the firmware volume in an FD binary")
parser.add_argument('-r', '--replace', nargs="+", help="The replace command combines the functionality of remove and \
                                                       add into a single operation.")


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


def parser_command_line(args, logger):
    """parser command lines"""
    # parser "-v, --view"
    if args.view:
        # call view image function
        pass

    # parser "-d, --delete"
    if args.delete:
        delete_arg_list = args.delete
        if len(delete_arg_list) < 3 or ((len(delete_arg_list)-3) % 2 != 1 and len(delete_arg_list) != 3):
            logger.error("FMMT", "Invalid parameter, Please make sure the parameter is correct.")
            os.system(sys.executable + ' ' + os.path.join(os.path.dirname(__file__), "FMMT.py") + ' ' + '-h')
            return 0

        elif len(delete_arg_list) == 3:
            # Delete entire FV in an FD image file.
            # search input file check whether it exist or not
            if not glob.glob(os.path.join(os.path.dirname(__file__), delete_arg_list[0])):
                logger.error("FMMT", "Please make sure the %s exist!" % args.delete[0])
                print("Please make sure the %s exist!" % delete_arg_list[0])
                return 0

            # input binary file exist.
            input_binary_file = os.path.join(os.path.dirname(__file__), delete_arg_list[0])
            FvId = delete_arg_list[1]
            fileName = delete_arg_list[2]

        elif (len(delete_arg_list)-3) % 2 == 1:
            # Delete some FFS file.
            input_binary_file = os.path.join(os.getcwd(), delete_arg_list[0])
            FvIds = delete_arg_list[1:-1:2]
            fileNames = delete_arg_list[2:-1:2]
            output_binary_file = os.path.join(os.getcwd(), delete_arg_list[-1])
            if not os.path.exists(output_binary_file):
                # This judge delete after write output file.
                os.mknod(output_binary_file)
            for Fvid, fileName in zip(FvIds, fileNames):
                pass
            return

    # parser "-a, --add"
    if args.add:
        add_arg_list = args.add
        if (len(add_arg_list) - 3) % 2 == 1 and len(add_arg_list) > 3:
            pass
            return

        else:
            logger.error("Invalid parameter, Please make sure the parameter is correct.")
            os.system(sys.executable + ' ' + os.path.join(os.path.dirname(__file__), "FMMT.py") + ' ' + '-h')
            return 0

    # parser "-r, --replace"
    if args.replace:
        replace_arg_list = args.replace
        if len(replace_arg_list) > 4 and (len(replace_arg_list)-2) % 3 == 0:
            pass
        else:
            logger.error("Invalid parameter, Please make sure the parameter is correct.")
            os.system(sys.executable + ' ' + os.path.join(os.path.dirname(__file__), "FMMT.py") + ' ' + '-h')
            return 0

def main():
    args = parser.parse_args()
    status = 0

    logger = logging.getLogger('FMMT')
    logger.setLevel(logging.DEBUG)

    lh = logging.StreamHandler(sys.stdout)
    lf = logging.Formatter("%(asctime)s- %(levelname)-8s: %(message)s")
    lh.setFormatter(lf)
    logger.addHandler(lh)
    # parser command line
    status = parser_command_line(args, logger)
    if not status:
        logger.error("Error parser command lines")
        return status
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
