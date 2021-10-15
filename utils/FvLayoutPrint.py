## @file
# This file is used to define the printer for Bios layout.
#
# Copyright (c) 2021-, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

def GetFormatter(layout_format):
    if layout_format == 'json':
        return JsonFormatter()
    elif layout_format == 'yaml':
        return YamlFormatter()
    elif layout_format == "html":
        return HtmlFormatter()
    else:
        return TxtFormatter()

class Formatter(object):
    def dump(self, layoutdict, outputfile = None):
        raise NotImplemented

class JsonFormatter(Formatter):
    def dump(self,layoutdict, outputfile = None):
        try:
            import json
        except:
            TxtFormatter().dump(layoutdict,outputfile)
            return
        print(outputfile)
        if outputfile:
            with open(outputfile,"w") as fw:
                json.dump(layoutdict, fw, indent=2)
        else:
            print(json.dumps(layoutdict,indent=2))

class TxtFormatter(Formatter):
    def dump(self,layoutdict, outputfile=None):
        pass

class YamlFormatter(Formatter):
    def dump(self,layoutdict, outputfile = None):
        TxtFormatter().dump(layoutdict,outputfile)

class HtmlFormatter(Formatter):
    def dump(self,layoutdict, outputfile = None):
        TxtFormatter().dump(layoutdict,outputfile)