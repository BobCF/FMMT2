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
import sys
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

def print_banner():
    print("")

class FMMT():
    def __init__(self):
        self.firmware_packet = {}

    def CheckFfsName(self, FfsName):
        try:
            return uuid.UUID(FfsName)
        except:
            return FfsName

    def View(self, inputfile, outputfile=None):
        # ParserFile(inputfile, outputfile, ROOT_TYPE)
        filetype = os.path.splitext(inputfile)[1].lower()
        if filetype == '.fd':
            ROOT_TYPE = ROOT_TREE
        elif filetype == '.fv':
            ROOT_TYPE = ROOT_FV_TREE
        elif filetype == '.ffs':
            ROOT_TYPE = ROOT_FFS_TREE
        elif filetype == '.sec':
            ROOT_TYPE = ROOT_SECTION_TREE
        else:
            ROOT_TYPE = ROOT_TREE
        ParserFile(inputfile, outputfile, ROOT_TYPE)

    def Delete(self, inputfile, TargetFfs_name, outputfile, Fv_name=None):
        if Fv_name:
            DeleteFfs(inputfile, self.CheckFfsName(TargetFfs_name), outputfile, uuid.UUID(Fv_name))
        else:
            DeleteFfs(inputfile, self.CheckFfsName(TargetFfs_name, outputfile))

    def Extract(self, inputfile, Ffs_name, outputfile):
        ExtractFfs(inputfile, self.CheckFfsName(Ffs_name), outputfile)

    def AddNew(self, inputfile, Fv_name, newffsfile, outputfile):
        AddNewFfs(inputfile, self.CheckFfsName(Fv_name), newffsfile, outputfile)

    def Replace(self,inputfile, Ffs_name, newffsfile, outputfile, Fv_name=None):
        if Fv_name:
            ReplaceFfs(inputfile, self.CheckFfsName(Ffs_name, newffsfile, outputfile, uuid.UUID(Fv_name)))
        else:
            ReplaceFfs(inputfile, self.CheckFfsName(Ffs_name, newffsfile, outputfile))


def main():
    args=parser.parse_args()
    status=0

    try:
        fmmt=FMMT()
        if args.View:
            fmmt.View(args.View[0])
        if args.Delete:
            fmmt.Delete(args.Delete[0],args.Delete[1],args.Delete[2],args.Delete[3])
        if args.Extract:
            fmmt.Extract(args.Extract[0],args.Extract[1],args.Extract[2])
        if args.Add:
            fmmt.Add(args.Add[0],args.Add[1],args.Add[2],args.Add[3])
        if args.Replace:
            fmmt.Replace(args.Replace[0],args.Replace[1],args.Replace[2],args.Replace[3])
        # TODO:
        '''Do the main work'''
    except Exception as e:
        print(e)

    return status


if __name__ == "__main__":
    exit(main())
