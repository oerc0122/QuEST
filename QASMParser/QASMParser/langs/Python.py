from QASMParser.QASMTypes import *

def set_lang():
    Variable.to_lang = Variable_to_python
    Argument.to_lang = Argument_to_python
    CallGate.to_lang = CallGate_to_python
    Comment.to_lang = Comment_to_python
    Measure.to_lang = Measure_to_python
    IfBlock.to_lang = IfBlock_to_python
    Gate.to_lang = CreateGate_to_python
    PyBlock.to_lang = PyBlock_to_python
    Loop.to_lang = Loop_to_python
    CBlock.to_lang = CBlock_to_python
    Reset.to_lang = Reset_to_python
    
def Reset_to_python(self):
    qarg = self._qargs[0]
    qindex = self._qargs[1]
    if not self._loops:
        return f'collapseToOutcome({qarg.name}, {qindex}, 0);'
    else:
        if self._loops.end == qarg.size:
            return f'initStateZero({qarg.name});'
        else:
            self.print_loops()

def Comment_to_python(self):
    return "#" + self.comment

def Variable_to_python(self):
    if self.classical: return f'{self.name} = [0]*{self.size}'
    else: return f'{self.name} = createQureg({self.size}, Env)'

def Argument_to_python(self):
    if self.classical: return f'{self.name}'
    else: return f'{self.name}, {self.name}_index'

def PyBlock_to_python(self):
    raise NotImplementedError('Cannot have python blocks yet')

def CallGate_to_python(self):
    if self.name in Gate.internalGates:
        gateRef   = Gate.internalGates[self.name]
        preString, printArgs = gateRef.reorder_args(self._qargs,self._cargs)
        printGate = gateRef.internalName
    else:
        printArgs = ", ".join([f"{qarg[0].name}, {qarg[1]}" for qarg in self._qargs])
        for carg in self._cargs:
            printArgs += ", "+carg
        printGate = self.name
        preString = []
    
    outString = ""
    indent = "  "
    depth = 0
    
    if self._loops:
        for line in preString:
            outString += indent*depth + line + "\n"
        outString += self.print_loops()
    else:
        for line in preString:
            outString += indent*depth + line + "\n"
        outString += f"{indent*depth+printGate}({printArgs})"
    return outString

def CBlock_to_python(self):
    print("Warning cBlock will not be parsed")
    return ""

def Measure_to_python(self):
    carg = self._cargs[0].name
    bindex = self._cargs[1]
    qarg = self._qargs[0]
    qindex = self._qargs[1]

    mainString = f"{carg}[{bindex}] = measure({qarg.name}, {qindex})"
    if self._loops:
        return self.print_loops()
    else:
        return mainString

def IfBlock_to_python(self):
    outStr = f"if ({self._cond}):"
    for line in self._code:
        outStr += "    "+line.to_lang()
    return outStr

def CreateGate_to_python(self):
    printArgs = ", ".join([f"{qarg}, {qarg}_index" for qarg in self._qargs])
    for carg in self._cargs:
        printArgs += ", "+carg
    outStr = f"def {self.name}({printArgs}) :\n"
    for line in self._code:
        outStr += "    "+line.to_lang() +"\n"
    return outStr

def Loop_to_python(self):
    forBlockOpen = "for {var} in range({start},{end},{step}):\n"
    indent = "    "
    forBlockClose = ""
    lineEnd = "\n"
        
    outString = forBlockOpen.format(var = self.var, start = self.start, end = self.end, step = self.step)
    for line in self._code:
        outString += f"{indent}{line.to_lang()} \n"
    outString += forBlockClose + "\n"
    return outString
