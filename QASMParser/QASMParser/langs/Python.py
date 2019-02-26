from QASMParser.QASMTypes import *

def set_lang():
    Variable.to_lang = Variable_to_python
    Argument.to_lang = Argument_to_python
    CallGate.to_lang = CallGate_to_python
    Comment.to_lang = Comment_to_python
    Measure.to_lang = Measure_to_python
    IfBlock.to_lang = IfBlock_to_python
    Gate.to_lang = CreateGate_to_python

    
def Comment_to_python(self):
    return "#" + self.comment

def Variable_to_python(self):
    if self.classical: return f'{self.name} = [0]*{self.size}'
    else: f'{self.name} = createQureg({self.size}, Env)'

def Argument_to_python(self):
    return self.name

def CallGate_to_python(self):
    if self._loops:
        return ""
    else:
        printArgs = ", ".join([f"{qarg[0].name}, {qarg[1]}" for qarg in self._qargs])
        for carg in self._cargs:
            printArgs += ", "+carg
        return f"{self.gate}({printArgs})"

def Measure_to_python(self):
    return f"{self.carg.name}[{self.bindex}] = measure({self.qarg.name}, {self.qindex})"

def ExternalBlock_to_python(self):
    raise NotImplementedError('Cannot convert external C Block to Python')

def IfBlock_to_python(self):
    printArgs = ",".join([arg.to_lang() for arg in self._qargs + self._cargs])
    outSTr = f"if ({self._cond}):"
    for line in self._code:
        outStr += "    "+line.to_lang()
    return outStr

def CreateGate_to_python(self):
    printArgs = ",".join([arg.to_lang() for arg in self._qargs + self._cargs])
    outSTr = f"def {self.name}({printArgs}):"
    for line in self._code:
        outStr += "    "+line.to_lang()
    return outStr

def Loop_to_python(self):
    forBlock = "for {var} in range({min},{max},{step}):\n"
    indent = "    "
    forBlockClose = ""
    lineEnd = "\n"
        
    outString = ""
    for loop in self._loops:
        outString += indent*depth + forBlockOpen.format(var = loop[0], min = loop[1][0], max = loop[1][1], step = 1)
        depth += 1
    outString += f"{indent*depth}{internal}" + lineEnd
    for loop in self._loops:
        depth -= 1
        outString += indent*depth + forBlockClose + "\n"
    return outString
