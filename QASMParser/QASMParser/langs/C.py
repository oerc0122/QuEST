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
    InitEnv.to_lang = init_env

# Several details pertaining to the language in question
hoistFuncs = True   # Move functions to front of program
hoistVars  = False  # Move variables to front of program
bareCode   = False  # Can code be bare or does it need to be in function
blockOpen = "{"     # Block delimiters
blockClose = "}"    #  ""      ""
indent = "  "       # Standard indent depth

def include(filename):
    return f'#include "{filename}"'

def init_env(self):
    return f'QuESTEnv Env = createQuESTEnv();'

def Output_to_c(self):
    carg = self._cargs[0]
    bindex = self._cargs[1]
    return f'printf("%d ", {carg}[{bindex}]);'
    
def Reset_to_c(self):
    qarg = self._qargs
    qargRef = self.resolve_arg(qarg)
    return f'collapseToOutcome(qreg, {qargRef}, 0);'
    
def ClassicalRegister_to_c(self):
    return f'int {self.name}[{self.size}];'

def QuantumRegister_to_c(self):
    return f"Qureg {self.name} = createQureg({self.size}, Env);"

def Argument_to_c(self):
    if self.classical: return f'qreal {self.name}'
    else: return f'Qureg {self.name}, int {self.name}_index'

def Let_to_c(self):
    return f'const int {self.var} = {self.val};'
    
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
        if coreTokens.closeBlock(instruction): depth-=1
        outStr += indent*depth + instruction+"\n"
        if coreTokens.openBlock(instruction): depth+=1
        instruction = nextLine()
    return outStr
    
def CallGate_to_c(self):
    printArgs = ""
    if self._qargs:
        printArgs += "qreg, "
        printArgs += ", ".join([self.resolve_arg(qarg) for qarg in self._qargs])
    for carg in self._cargs:
        if printArgs:
            printArgs += ", "+carg
        else:
            printArgs = carg
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
    qarg = self._qargs
    qargRef = self.resolve_arg(qarg)
    return f"{carg}[{bindex}] = measure(qreg, {qargRef});"

def IfBlock_to_c(self):
    return f"if ({self._cond})"

def CreateGate_to_c(self):
    printArgs = ""
    if self._qargs:
        printArgs += "Qureg qreg"
        printArgs += ", " + ", ".join([f"int {qarg}_index" for qarg in self._qargs])
    for carg in self._cargs:
        if printArgs: printArgs += ", float "+carg
        else: printArgs += "float "+carg
    outStr = f"void {self.name}({printArgs})"
    return outStr

def Loop_to_c(self):
    return  f"for (int {self.var} = {self.start}; {self.var} < {self.end}; {self.var} += {self.step})"

