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
import logging
import sys
import re
from core.FMMTOperation import *

parser = argparse.ArgumentParser(description='''
View the Binary Structure of FD/FV/Ffs/Section, and Delete/Extract/Add/Replace a Ffs from/into a FV.
''')
parser.add_argument("--version", action="version", version='%(prog)s Version 1.0',
                    help="Print debug information.")
parser.add_argument("-v", "--View", dest="View", nargs='+',
                    help="View each FV and the named files within each FV: '-v inputfile outputfile, inputfiletype(.Fd/.Fv/.ffs/.sec)'")
parser.add_argument("-d", "--Delete", dest="Delete", nargs='+',
                    help="Delete a Ffs from FV: '-d inputfile TargetFfsName outputfile TargetFvName(Optional)'")
parser.add_argument("-e", "--Extract", dest="Extract", nargs='+',
                    help="Extract a Ffs Info: '-e inputfile TargetFfsName outputfile'")
parser.add_argument("-a", "--Add", dest="Add", nargs='+',
                    help="Add a Ffs into a FV:'-a inputfile TargetFvName newffsfile outputfile'")
parser.add_argument("-r", "--Replace", dest="Replace", nargs='+',
                    help="Replace a Ffs in a FV: '-r inputfile TargetFfsName newffsfile outputfile'")

class FMMT():
    def __init__(self):
        self.firmware_packet = {}
    
    def CheckFfsName(self, FfsName):
        try:
            return uuid.UUID(FfsName)
        except:
            return FfsName

    def View(self, ParaList):
        # ParserFile(inputfile, outputfile, ROOT_TYPE)
        filetype = os.path.splitext(ParaList[0])[1]
        print(filetype)
        if re.search(filetype, '.Fd', re.IGNORECASE):
            ROOT_TYPE = ROOT_TREE
        elif re.search(filetype, '.Fv', re.IGNORECASE):
            ROOT_TYPE = ROOT_FV_TREE
        elif re.search(filetype, '.ffs', re.IGNORECASE):
            ROOT_TYPE = ROOT_FFS_TREE
        elif re.search(filetype, '.sec', re.IGNORECASE):
            ROOT_TYPE = ROOT_SECTION_TREE
        else:
            ROOT_TYPE = ROOT_TREE
        if len(ParaList) == 2:
            ParserFile(ParaList[0], ParaList[1], ROOT_TYPE)
        else:
            ParserFile(ParaList[0], None, ROOT_TYPE)

    def Delete(self, ParaList):
        # DeleteFfs(inputfile, TargetFfs_name, outputfile, Fv_name=None)
        if len(ParaList) == 4:
            DeleteFfs(ParaList[0], self.CheckFfsName(ParaList[1]), ParaList[2], uuid.UUID(ParaList[3]))
        else:
            DeleteFfs(ParaList[0], self.CheckFfsName(ParaList[1]), ParaList[2])

    def Extract(self, ParaList):
        # ExtractFfs(inputfile, Ffs_name, outputfile)
        ExtractFfs(ParaList[0], self.CheckFfsName(ParaList[1]), ParaList[2])

    def Add(self, ParaList):
        # AddNewFfs(inputfile, Fv_name, newffsfile, outputfile)
        AddNewFfs(ParaList[0], self.CheckFfsName(ParaList[1]), ParaList[2], ParaList[3])

    def Replace(self, ParaList):
        # ReplaceFfs(inputfile, Ffs_name, newffsfile, outputfile, Fv_name=None)
        if len(ParaList) == 5:
            ReplaceFfs(ParaList[0], self.CheckFfsName(ParaList[1]), ParaList[2], ParaList[3], uuid.UUID(ParaList[4]))
        else:
            ReplaceFfs(ParaList[0], self.CheckFfsName(ParaList[1]), ParaList[2], ParaList[3])

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
        if args.View:
            fmmt.View(args.View)
        if args.Delete:
            fmmt.Delete(args.Delete)
        if args.Extract:
            fmmt.Extract(args.Extract)
        if args.Add:
            fmmt.Add(args.Add)
        if args.Replace:
            fmmt.Replace(args.Replace)
        # TODO:
        '''Do the main work'''
    except Exception as e:
        print(e)

    return status


if __name__ == "__main__":
    exit(main())
