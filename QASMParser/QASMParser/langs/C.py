from QASMParser.QASMTypes import *
from QASMParser.QASMTokens import coreTokens

def set_lang():
    Variable.to_lang = Variable_to_c
    Argument.to_lang = Argument_to_c
    CallGate.to_lang = CallGate_to_c
    Comment.to_lang = Comment_to_c
    Measure.to_lang = Measure_to_c
    IfBlock.to_lang = IfBlock_to_c
    Gate.to_lang = CreateGate_to_c
    CBlock.to_lang = CBlock_to_c
    Loop.to_lang = Loop_to_c
    Reset.to_lang = Reset_to_c

def Reset_to_c(self):
    qarg = self._qargs[0]
    qindex = self._qargs[1]
    if not self._loops:
        return f'collapseToOutcome({qarg.name}, {qindex}, 0);'
    else:
        if self._loops.end == qarg.size:
            return f'initStateZero({qarg.name});'
        else:
            self.print_loops()
    return ""
    
def Variable_to_c(self):
    if self.classical: return f'int[{self.size}] {self.name};'
    else: return f"Qureg {self.name} = createQureg({self.size}, Env);"

def Argument_to_c(self):
    if self.classical: return f'qreal {self.name}'
    else: return f'Qureg {self.name}, int {self.name}_index'

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
    indent = "  "
    depth = 0
    
    if self._loops:
        for line in preString:
            outString += indent*depth + line + ";\n"
        outString += self.print_loops()
    else:
        for line in preString:
            outString += indent*depth + line + ";\n"
        outString += f"{indent*depth+printGate}({printArgs});"
    return outString

def Comment_to_c(self):
    return "//" + self.comment

def Measure_to_c(self):
    carg = self._cargs[0].name
    bindex = self._cargs[1]
    qarg = self._qargs[0]
    qindex = self._qargs[1]

    mainString = f"{carg}[{bindex}] = measure({qarg.name}, {qindex})"
    if self._loops:
        return self.print_loops()
    else:
        return mainString

def IfBlock_to_c(self):
    outStr = f"if ({self._cond})\n{{\n"
    for line in self._code:
        outStr += "  "+line.to_lang()
    outStr += "}"
    return outStr

def CreateGate_to_c(self):
    printArgs = ", ".join([f"{qarg}, {qarg}_index" for qarg in self._qargs])
    for carg in self._cargs:
        printArgs += ", "+carg
    outStr = f"void {self.name}({printArgs}) {{\n"
    for line in self._code:
        outStr += "  "+line.to_lang() +"\n"
    outStr += "}"
    return outStr

def Loop_to_c(self):
    forBlockOpen = "for (int {var} = {start}; {var} < {end}; {var} += {step})\n{{\n"
    indent = "  "
    forBlockClose = "}"
    lineEnd = ";\n"
        
    outString = forBlockOpen.format(var = self.var, start = self.start, end = self.end, step = self.step)
    for line in self._code:
        outString += f"{indent}{line.to_lang()} \n"
    outString += forBlockClose + "\n"
    return outString
