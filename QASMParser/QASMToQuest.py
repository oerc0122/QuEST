#!/usr/bin/env python3

from QASMParser.QASMParser import *
import QASMParser.QASMQuESTGate
myProg = Prog('./test.qasm')
myProg.to_c("test.c")
