from .QASMParser import *
from copy import copy
# def __init__(self, filename, noFile = False):
# def __init__(self, name, cargs, qargs, block, QuESTGate = False, internalName = None):
# def __init__(self, parentName, startline, block):

class QuESTLibGate(Gate):
    def __init__(self, name, cargs, qargs, argOrder, internalName):
        self.name = name
        self._cargs = {}
        self._qargs = {}
        self._qargs = self.parse_qarg_string(qargs)
        self.internalName = internalName
        self.argOrder = argOrder
        Gate.gates[self.name] = self
        Gate.internalGates[self.name] = self
        
    def parse_qarg_string(self, qargString):
        qargs = [ coreTokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        qargs = [[arg[0], arg[0]+"_index"] for arg in qargs]
        return qargs
        
    def reorder_args(self, qargsIn, cargsIn):
        qargs = copy(qargsIn)
        cargs = copy(cargsIn)
        argString = ""
        preString = []
        args = []
        rest = []
        for expect in self.argOrder:
            if expect == "nextQureg":
                qarg = qargs.pop(0)
                args.append(qarg[0].name)
            elif expect == "index":
                args.append(str(qarg[1]))
            elif expect == "nextIndex":
                qarg = qargs.pop(0)
                args.append(str(qarg[1]))
        if "mConRestIndex" in self.argOrder:
            for qarg in qargs:
                rest.append(qarg[1])
        nTemp = 0
        for arg in self.argOrder:
            if arg == "nextQureg" or arg == "nextIndex" or arg == "index":
                argString += ","+args.pop(0)
            elif arg == "mConRestIndex":
                nTemp+=1
                tempVar = "tmp"+str(nTemp)
                nRest     = len(rest)
                preString += [f"int[{nRest}] {tempVar} = {{"+",".join(rest)+"}"]
                argString += f", (int*){tempVar}, {nRest}"
            elif arg == "nextCarg":
                argString += f"{cargs.pop(0)}"
            elif arg == "cargs":
                argString += f",{','.join(cargs)}"
                cargs = []
            elif arg == "complexCarg":
                nTemp += 1
                tempVar = "tmp"+str(nTemp)
                tempArg = [cargs.pop(0), cargs.pop(0)]
                preString += [f"Complex {tempVar} = {{{','.join(tempArg)}}}"]
                argString += f",{tempVar}"
            elif arg == "complexMatrix2Carg":
                nTemp += 1
                tempVar = "tmp"+str(nTemp)
                tempArg = [cargs.pop(0), cargs.pop(0), cargs.pop(0), cargs.pop(0)]
                preString += [f"ComplexMatrix2 {tempVar} = {{{','.join(tempArg)}}}"]
                argString += f",{tempVar}"
            elif arg == "not":
                nTemp += 1
                tempVar = "not"
                preString += [f"ComplexMatrix2 {tempVar} = {{0., 1., 1., 0.}}"]
                argString += ","+tempVar
        return preString, argString.strip(',')
                
    def to_c(self):
        pass
        
#[ 0 1 1 0]

    
QuESTLibGate(name = "x",   cargs = None, qargs = "a", argOrder = ("nextQureg", "index"), internalName = "pauliX")
QuESTLibGate(name = "cx",  cargs = None, qargs = "a", argOrder = ("nextQureg", "index", "nextIndex"), internalName = "controlledNot")
QuESTLibGate(name = "ccx", cargs = None, qargs = "a,b,c", argOrder = ("nextQureg", "mConRestIndex", "index", "not"), internalName = "multiControlledUnitary")
QuESTLibGate(name = "rotateX", cargs = "phi", qargs = "a", argOrder = ("nextQureg", "index", "cargs"), internalName = "rotateX")
QuESTLibGate(name = "rotateY", cargs = "theta", qargs = "a", argOrder = ("nextQureg", "index", "cargs"), internalName = "rotateY")
QuESTLibGate(name = "rotateZ", cargs = "lambda", qargs = "a", argOrder = ("nextQureg", "index", "cargs"), internalName = "rotateZ")

