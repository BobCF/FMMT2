# FMMT
## Overview
This FMMT tool is the python implementation of the edk2 FMMT tool which locates at https://github.com/tianocore/edk2-staging/tree/FceFmmt.
This implementation has the same usage as the edk2 FMMT, but it's more readable and relaiable.

## Usage
The target of this implementation is to be included in the edk2 Basetools, so this FMMT tool need to work in edk2 environment.
The following instructions need to be done before using this FMMT.
1. Clone this repo and rename the folder name from FMMT2 to FMMT.
2. Clone edk2 repo https://github.com/tianocore/edk2.git
3. Copy FMMT folder to edk2/BaseTools/Source/Python
4. Copy FMMT/BinWrappers/WindowsLike/FMMT.bat to edk2/BaseTools/BinWrappers/WindowsLike
5. Copy FMMT/BinWrappers/PosixLike/FMMT to edk2/BaseTools//BinWrappers/PosixLike
6. go to edk2 folder
7. Execute "edksetup rebuild"
8. Use FMMT directly. For example, "FMMT -h"
