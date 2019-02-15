#!/usr/bin/env python3

import argparse
from QASMParser.QASMParser import *
import QASMParser.QASMQuESTGate

parser = argparse.ArgumentParser(description='QASM parser to translate from QASM to QuEST input', add_help=True)
parser.add_argument('sources', nargs=argparse.REMAINDER, help="List of sources to compile")
parser.add_argument('-o','--output', help="File to compile to")
argList = parser.parse_args()

if len(argList.sources) > 1: raise NotImplementedError('Cannot compile multiple sources')
if len(argList.sources) == 0:
    parser.print_help()
    quit()

for source in argList.sources:
    myProg = Prog(source)
myProg.to_c(argList.output)
