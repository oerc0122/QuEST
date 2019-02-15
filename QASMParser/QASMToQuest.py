#!/usr/bin/env python3

from QASMParser.QASMParser import *
import QASMParser.QASMQuESTGate

from QASMParser.cli import get_command_args
argList = get_command_args()

for source in argList.sources:
    myProg = ProgFile(source)
myProg.to_c(argList.output)
