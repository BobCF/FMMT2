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
        # TODO:
        '''Do the main work'''
    except Exception as e:
        print(e)

    return status


if __name__ == "__main__":
    exit(main())
