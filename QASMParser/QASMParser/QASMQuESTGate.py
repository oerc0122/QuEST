from .QASMParser import *
from copy import copy

class QuESTArg(Referencable):
    def __init__(self, name, val, type_):
        self.name = name
        self.val = val
        self.type_ = type_

class QuESTLibGate(Gate):
    def __init__(self, name, cargs, qargs, argOrder, internalName):
        self.type_ = "Gate"
        self.name = name
        self._cargs = {}
        self._qargs = {}
        self._qargs = self.parse_qarg_string(qargs)
        self.internalName = internalName
        self.argOrder = argOrder
        Gate.internalGates[self.name] = self

    def parse_qarg_string(self, qargString):
        qargs = [ coreTokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        qargs = [[arg[0], arg[0]+"_index"] for arg in qargs]
        return qargs

    def reorder_args(self, qargs, cargs):
        preString = []
        args = []
        outCargs = []
        for expect in self.argOrder:
            if expect == "nextQureg":
                args.append('qreg')
                # qarg = qargs.pop(0)
                # args.append(qarg[0].name)
            elif expect == "nextIndex":
                qarg = qargs.pop(0)
                args.append(Operation.resolve_arg(self,qarg))
            elif expect[0:6] == "nIndex":
                nArgs = expect[6:]
                if not nArgs.isdecimal() :
                    if nArgs != "*":
                        raise TypeError('Expected number of indices')
                    else:
                        nArgs = len(qargs)
                nArgs = int(nArgs)
                tmp = []
                for i in range(nArgs):
                    qarg = qargs.pop(0)
                    tmp.append(Operation.resolve_arg(self,qarg))
                args.append(tmp)
        nTemp = 0
        for arg in self.argOrder:
            if arg == "nextQureg" or arg == "nextIndex" or arg == "index":
                outCargs += [args.pop(0)]
            elif arg[0:6] == "nIndex":
                indices = args.pop(0)
                nTemp+=1
                tempVar = "tmp"+str(nTemp)
                nIndices     = len(indices)
                preString += [f"int {tempVar}[{nIndices}] = {{"+",".join(indices)+"};"]
                outCargs += [f"(int*) {tempVar}",f"{nIndices}"]
            elif arg == "nextCarg":
                outCargs += [cargs.pop(0)]
            elif arg == "cargs":
                outCargs += cargs
                cargs = []
            elif arg == "complexCarg":
                nTemp += 1
                tempVar = "tmp"+str(nTemp)
                tempArg = [cargs.pop(0), cargs.pop(0)]
                preString += [f"Complex {tempVar} = {{{','.join(tempArg)}}};"]
                outCargs += [tempVar]
            elif arg == "complexMatrix2Carg":
                nTemp += 1
                tempVar = "tmp"+str(nTemp)
                tempArg = [cargs.pop(0), cargs.pop(0), cargs.pop(0), cargs.pop(0)]
                preString += [f"ComplexMatrix2 {tempVar} = {{{','.join(tempArg)}}};"]
                outCargs += [tempVar]
            elif arg == "not":
                nTemp += 1
                tempVar = "not"
                preString += [
                    f"ComplexMatrix2 {tempVar};",
                    f"{tempVar}.r0c0 = (Complex) {{.real=0., .imag=0.}};",
                    f"{tempVar}.r0c1 = (Complex) {{.real=1., .imag=0.}};",
                    f"{tempVar}.r1c0 = (Complex) {{.real=1., .imag=0.}};",
                    f"{tempVar}.r1c1 = (Complex) {{.real=0., .imag=0.}};"
                ]
                outCargs += [tempVar]
        return preString, outCargs

QuESTLibGate(name = "x",   cargs = None, qargs = "a", argOrder = ("nextQureg", "nextIndex"), internalName = "pauliX")
QuESTLibGate(name = "cx",  cargs = None, qargs = "a", argOrder = ("nextQureg", "nextIndex", "nextIndex"), internalName = "controlledNot")
QuESTLibGate(name = "ccx", cargs = None, qargs = "a,b,c", argOrder = ("nextQureg", "nIndex2", "nextIndex", "not"), internalName = "multiControlledUnitary")
QuESTLibGate(name = "rotateX", cargs = "phi", qargs = "a", argOrder = ("nextQureg", "nextIndex", "cargs"), internalName = "rotateX")
QuESTLibGate(name = "rotateY", cargs = "theta", qargs = "a", argOrder = ("nextQureg", "nextIndex", "cargs"), internalName = "rotateY")
QuESTLibGate(name = "rotateZ", cargs = "lambda", qargs = "a", argOrder = ("nextQureg", "nextIndex", "cargs"), internalName = "rotateZ")
