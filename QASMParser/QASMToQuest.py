#!/usr/bin/env python3
from QASMParser.QASMParser import *
import QASMParser.QASMQuESTGate
from QASMParser.cli import get_command_args
argList = get_command_args()

for source in argList.sources:
    myProg = ProgFile(source)

if argList.language:
    lang = argList.language
elif argList.output.endswith('.py'):
    lang = "Python"
elif argList.output.endswith('.c'):
    lang = "C"
elif not argList.output:
    raise IOError('Neither language nor output specified')

if argList.output:
    outputFile = argList.output
else:
    outputFile = None

myProg.to_lang(outputFile, lang)
