from QASMParser.QASMTypes import *
from QASMParser.QASMTokens import coreTokens

def set_lang():
    ClassicalRegister.to_lang = ClassicalRegister_to_c
    QuantumRegister.to_lang = QuantumRegister_to_c
    Let.to_lang = Let_to_c
    Argument.to_lang = Argument_to_c
    CallGate.to_lang = CallGate_to_c
    Comment.to_lang = Comment_to_c
    Measure.to_lang = Measure_to_c
    IfBlock.to_lang = IfBlock_to_c
    Gate.to_lang = CreateGate_to_c
    CBlock.to_lang = CBlock_to_c
    Loop.to_lang = Loop_to_c
    NestLoop.to_lang = Loop_to_c
    Reset.to_lang = Reset_to_c

blockOpen = "{"
blockClose = "}"
indent = "  "

def Reset_to_c(self):
    qarg = self._qargs[0]
    qindex = self._qargs[1]
    return f'collapseToOutcome({qarg.name}, {qindex}, 0);'
    
def ClassicalRegister_to_c(self):
    return f'int[{self.size}] {self.name};'

def QuantumRegister_to_c(self):
    return f"Qureg {self.name} = createQureg({self.size}, Env);"

def Argument_to_c(self):
    if self.classical: return f'qreal {self.name}'
    else: return f'Qureg {self.name}, int {self.name}_index'

def Let_to_c(self):
    return f'const int {self.var} = {self.val}'
    
def CBlock_to_c(self):
    outStr = ""
    indent = "  "
    depth = 0
    nextLine = self.currentFile.readline
    instruction = nextLine()
    while instruction:
        if instruction.startswith('for'):
            instruction += nextLine()
            instruction += nextLine()
            instruction = instruction.strip(';')
        instruction = re.sub('([{}]);','\g<1>',instruction)
        if coreTokens.closeBlock(instruction): depth-=1
        outStr += indent*depth + instruction+"\n"
        if coreTokens.openBlock(instruction): depth+=1
        instruction = nextLine()
    return outStr
    
def CallGate_to_c(self):
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
    for line in preString:
        outString += line + ";\n"
    outString += f"{printGate}({printArgs});"
    return outString

def Comment_to_c(self):
    return "//" + self.comment

def Measure_to_c(self):
    carg = self._cargs[0].name
    bindex = self._cargs[1]
    qarg = self._qargs[0]
    qindex = self._qargs[1]

    return f"{carg}[{bindex}] = measure({qarg.name}, {qindex})"

def IfBlock_to_c(self):
    return f"if ({self._cond})"

def CreateGate_to_c(self):
    printArgs = ", ".join([f"{qarg}, {qarg}_index" for qarg in self._qargs])
    for carg in self._cargs:
        printArgs += ", "+carg
    outStr = f"void {self.name}({printArgs})"
    return outStr

def Loop_to_c(self):
    return  f"for (int {self.var} = {self.start}; {self.var} < {self.end}; {self.var} += {self.step})"

