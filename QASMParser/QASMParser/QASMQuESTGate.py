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
        rest = []
        for expect in self.argOrder:
            if expect == "nextQureg":
                args.append('qreg')
                qarg = qargs.pop(0)
                # args.append(qarg[0].name)
            elif expect == "index":
                args.append(Operation.resolve_arg(self,qarg))
            elif expect == "nextIndex":
                qarg = qargs.pop(0)
                args.append(Operation.resolve_arg(self,qarg))
        if "mConRestIndex" in self.argOrder:
            for qarg in qargs:
                rest += [qarg[1]]
        nTemp = 0
        for arg in self.argOrder:
            if arg == "nextQureg" or arg == "nextIndex" or arg == "index":
                outCargs += [args.pop(0)]
            elif arg == "mConRestIndex":
                nTemp+=1
                tempVar = "tmp"+str(nTemp)
                nRest     = len(rest)
                preString += [f"int {tempVar}[{nRest}] = {{"+",".join(rest)+"};"]
                outCargs += [f"(int*) {tempVar}",f"{nRest}"]
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

QuESTLibGate(name = "x",   cargs = None, qargs = "a", argOrder = ("nextQureg", "index"), internalName = "pauliX")
QuESTLibGate(name = "cx",  cargs = None, qargs = "a", argOrder = ("nextQureg", "index", "nextIndex"), internalName = "controlledNot")
QuESTLibGate(name = "ccx", cargs = None, qargs = "a,b,c", argOrder = ("nextQureg", "mConRestIndex", "index", "not"), internalName = "multiControlledUnitary")
QuESTLibGate(name = "rotateX", cargs = "phi", qargs = "a", argOrder = ("nextQureg", "index", "cargs"), internalName = "rotateX")
QuESTLibGate(name = "rotateY", cargs = "theta", qargs = "a", argOrder = ("nextQureg", "index", "cargs"), internalName = "rotateY")
QuESTLibGate(name = "rotateZ", cargs = "lambda", qargs = "a", argOrder = ("nextQureg", "index", "cargs"), internalName = "rotateZ")
