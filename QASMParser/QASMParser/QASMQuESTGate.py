from .QASMParser import *
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
        qargs = [ tokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        qargs = [[arg[0], arg[0]+"_index"] for arg in qargs]
        return qargs
        
    def reorder_args(self, qargs, cargs):
        argString = ""
        preString = ""
        args = []
        rest = []
        for expect in self.argOrder:
            if expect == "nextQureg":
                qarg = qargs.pop(0)
                args.append(qarg[0].name)
            elif expect == "Index":
                args.append(str(qarg[1]))
            elif expect == "nextIndex":
                qarg = qargs.pop(0)
                args.append(str(qarg[1]))
        if "mConRestIndex" in self.argOrder:
            for qarg in qargs:
                rest.append(qarg[1])

        for arg in self.argOrder:
            if arg == "nextQureg" or arg == "nextIndex" or arg == "Index":
                argString += ","+args.pop(0)
            elif arg == "mConRestIndex":
                nRest     = len(rest)
                preString = f"int[{nRest}] tmp = {{"+",".join(rest)+"};"
                argString += f", (int*)tmp, {nRest}"
        if cargs: argString += ",{','.join(cargs)}"

        return preString, argString.strip(',')
                
    def to_c(self):
        pass
        

QuESTLibGate(name = "x",   cargs = None, qargs = "a", argOrder = ("nextQureg", "Index"), internalName = "pauliX")
QuESTLibGate(name = "cx",  cargs = None, qargs = "a", argOrder = ("nextQureg", "Index", "nextIndex"), internalName = "controlledNot")
QuESTLibGate(name = "ccx", cargs = None, qargs = "a,b", argOrder = ("nextQureg", "mConRestIndex", "Index"), internalName = "multiControlledNot")
