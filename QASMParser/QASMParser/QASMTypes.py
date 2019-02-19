from .QASMErrors import *
from .QASMTokens import *
from .FileHandle import QASMFile, QASMBlock
import copy

class VarHandler:
    def __init__(self, qargs = None, cargs = None):
        self._loops = None
        self._qargs = qargs
        self._cargs = cargs

    def add_loop(self, index, start, end):
        if self._loops:
            self._loops = NestLoop(self._loops, index, start, end)
        else:
            self._loops = NestLoop(self, index, start, end)

    def print_loops(self):
        loops = self._loops
        self._loops = None
        outString = loops.to_lang()
        self._loops = loops
        return outString
            
    def handle_loops(self, pargs, slice = None):
        for parg in pargs:
            index = parg[1]
            if index is None:
                index = parg[0].name + "_index"
                self.add_loop(index, 1, parg[0].size)
                
            elif isinstance(index, str):
                pargSplit = index.split(':')
                if len(pargSplit) == 1: # Just index
                    if pargSplit[0].isdecimal():
                        index = int(pargSplit[0])
                    else: # Do nothing, assume the variable is fine
                        pass
                    
                elif len(pargSplit) == 2: # Min Max
                    index = parg[0].name + "_index"
                    pargMin = 1
                    pargMax = parg[0].size
                    if pargSplit[0]: pargMin = int(pargSplit[0])
                    if pargSplit[1]: pargMax = int(pargSplit[1])
                    self.add_loop(index, pargMin, pargMax)
                    
                else: raise IOError('Bad Index syntax')
        
                
    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))
                
class Comment:
    def __init__(self, comment):
        self.name = comment
        self.comment = comment

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

        
class Variable:
    def __init__(self, name, size, classical):
        self.name = name
        self.size = int(size)
        self.classical = classical

    def __repr__(self):
        return f"{self.name}[{self.size}]"

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class Argument:
    def __init__(self, name, classical):
        self.name = name
        self.classical = classical

    def __repr__(self):
        if classical: return self.name
        else: return self.name

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class CallGate(VarHandler):
    def __init__(self, gate, cargs, qargs):
        self.name = gate
        VarHandler.__init__(self, qargs, cargs)
        self.handle_loops(self._qargs)
        if cargs: self._cargs = cargs.split(',')
        else: self._cargs = []

    def __repr__(self):
        return f"{self.gate}({','.join(self._cargs)}) {self._qargs}"

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class Measure(VarHandler):
    def __init__(self, qarg, carg):
        VarHandler.__init__(self, qarg, carg)
        self.handle_loops([self._qargs])
        carg = self._cargs[0]
        bindex = self._cargs[1]
        qarg = self._qargs[0]
        qindex = self._qargs[1]
        
        if bindex is None:
            if carg.size < qarg.size:
                raise IOError(argSizeWarning.format(Req=qarg.size, Var=carg.name, Var2 = qarg.name, Max=carg.size))
            if carg.size > qarg.size:
                raise IOError(argSizeWarning.format(Req=carg.size, Var=qarg.name, Var2 = carg.name, Max=qarg.size))
            self._cargs[1] = self._qargs[1]
        
    def __repr__(self):
        return f"measure {self.qarg}[{self.qindex}] -> {self.carg}[{self.bindex}]"

class Reset(VarHandler):
    def __init__(self, qarg):
        VarHandler.__init__(self, qarg)
        self.handle_loops([self._qargs])

    def __repr__(self):
        return f"reset {self.qarg}[{self.qindex}]"

class CodeBlock:
    def __init__(self, block):
        self._code = []
        self._qargs= {}
        self._cargs= {}
        self._funcs= copy.copy(Gate.gates)
        self.currentFile = block
        self.instructions = self.currentFile.read_instruction()
        self._error = self.currentFile._error
        QASMType = self.currentFile.version[0]
        if QASMType == "OPENQASM":
            self.tokens = openQASM
        elif QASMType == "OAQEQASM":
            self.tokens = OAQEQASM
        else:
            self._error(QASMWarning.format(QASMType))
            
    def to_lang(self, filename):
        for line in self._code:
            return line.to_lang()

    def comment(self, comment):
        self._code += [Comment(comment)]

    def new_variable(self, argName, size, classical):
        variable = Variable(argName, size, classical)
        if variable in self._cargs or variable in self._qargs or variable in self._funcs:
            raise OSError(dupWarning.format(Type = "Variable", Name = variable.name))
        self._code += [variable]
        if variable.classical: self._cargs[variable.name] = variable
        else:                  self._qargs[variable.name] = variable

    def gate(self, funcName, cargs, qargs, block, recursive = None, opaque = None):
        if funcName in self._funcs: raise self._error(dupWarning.format('Gate', gate))
        gate = Gate(funcName, cargs, qargs, block, recursive, opaque)
        self._funcs[gate.name] = gate
        self._code += [gate]

    def call_gate(self, funcName, cargs, qargs):
        qargs = self.parse_qarg_string(qargs)
        if funcName not in self._funcs: self._error(existWarning.format(Type = 'Gate', Name = funcName))
        gate = CallGate(funcName, cargs, qargs)
        self._code += [gate]

    def measurement(self, qarg, qindex, carg, bindex):
        if carg not in self._cargs : self._error(existWarning.format(Type = 'Creg', Name = carg))
        else : carg = self._cargs[carg]
        if bindex:
            bindex = int(bindex)
            if bindex > carg.size - 1 or bindex < 0 :
                self._error(indexWarning.format(Var=carg,Req=bindex,Max=carg.size))

        if qarg not in self._qargs : self._error(existWarning.format(Type = 'Qreg', Name = qarg))
        else : qarg = self._qargs[qarg]
        if qindex:
            qindex = int(qindex)
            if qindex > qarg.size - 1 or qindex < 0 :
                self._error(indexWarning.format(Var=qarg,Req=qindex,Max=qarg.size))

        measure = Measure( [qarg, qindex], [carg, bindex] )
        
        self._code += [measure]

    def _resolve(self, var, type_, reason = ""):
        if type_ == "Index":
            if var in self._cargs: return self._cargs[var]
            elif tokens.int(var): return int(var)
            elif tokens.float(var): self._error(argWarning.format(reason, "index", "float"))
            elif var in self._qargs:  self._error(argWarning.format(reason, "index", "qreg"))
            else: self._error(argWarning.format(reason, "Index", "Unknown"))

    def add_reset(self, qarg, qindex):
        if qarg not in self._qargs : self._error(existWarning.format(Type = 'Qreg', Name = qarg))
        else : qarg = self._qargs[qarg]
        if qindex:
            qindex = int(qindex)
            if qindex > qarg.size - 1 or qindex < 0 :
                self._error(indexWarning.format(Var=qarg,Req=qindex,Max=qarg.size))

        reset = Reset( [qarg, qindex] )
        
        self._code += [reset]
            
    def new_if(self, cond, block):
        self._code += [IfBlock(cond, block)]

    def cBlock(self, block):
        self._code += [CBlock(block)]

    def parse_line(self, line, token):
        match = token(line)
        if token.name == "include":
            if hasattr(self,"include"):
                self.include(match.group('filename'))
            else:
                self._error(includeNotMain)
        elif token.name == "wholeLineComment":
            self.comment(match.group('comment'))
        elif token.name == "createReg":
            argName = match.group('qargName')
            size = match.group('qubitIndex')
            classical = match.group('regType') == "c"
            self.new_variable(argName, size, classical)
        elif token.name == "callGate":
            funcName = match.group('funcName')
            cargs = match.group('cargs')
            qargs = match.group('qargs')
            self.call_gate(funcName, cargs, qargs)
        elif token.name == "createGate":
            funcName = match.group('funcName')
            cargs = match.group('cargs')
            qargs = match.group('qargs')
            block = self.parse_block(funcName)
            self.gate(funcName, cargs, qargs, block)
        elif token.name == "createRGate":
            funcName = match.group('funcName')
            cargs = match.group('cargs')
            qargs = match.group('qargs')
            block = self.parse_block(funcName)
            self.gate(funcName, cargs, qargs, block, recursive = True)
        elif token.name == "opaque":
            funcName = match.group('funcName')
            cargs = match.group('cargs')
            qargs = match.group('qargs')
            block = self.parse_block(funcName)
            self.gate(funcName, cargs, qargs, block, opaque = True)
        elif token.name == "measure":
            carg = match.group('cargName')
            bindex = match.group('bitIndex')
            qarg = match.group('qargName')
            qindex = match.group('qubitIndex')
            self.measurement(qarg, qindex, carg, bindex)
        elif token.name == "ifLine":
            cond = match.group('cond')
            if match.group('op'):
                block = match.group('op')+";\n"
            else:
                block = self.parse_block("if")
            self.new_if(cond, block)
        elif token.name == "CBlock":
            block = self.parse_block("CBlock")
            self.cBlock(block)
        elif token.name == "PyBlock":
            block = self.parse_block("PyBlock")
            self.PyBlock(block)
        elif token.name == "barrier":
            pass
        elif token.name == "reset":
            qarg = match.group('qargName')
            qindex = match.group('qubitIndex')
            self.add_reset(qarg, qindex)
        else:
            self._error(instructionWarning.format(line.lstrip().split()[0], self.currentFile.QASMType))
        
    def parse_qarg_string(self, qargString):
        qargs = [ coreTokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        for qarg in qargs:
            if qarg[0] not in self._qargs: raise self._error(existWarning.format(Type = 'qreg', Name = qarg[0]))
        qargs = [[self._qargs[arg[0]], int(arg[1])] if arg[1] is not None and arg[1].isdecimal()
                 else [self._qargs[arg[0]], arg[1]]
                 for arg in qargs]
        return qargs

    def parse_instructions(self):
        for line in self.instructions:
            for token in self.tokens.tokens():
                if token(line) is not None:
                    self.parse_line(line, token)
                    break
            else: self._error('Invalid instruction: "'+line+'"')

    def parse_block(self, blockName):
        blockOpen = next(self.instructions)
        if not coreTokens.openBlock(blockOpen):
            self._error(f'{blockname} specification not followed by open block')
        depth = 1
        startline = self.currentFile.nLine
        block = ""
        for line in self.instructions:
            if coreTokens.openBlock(line):
                depth += 1
            elif coreTokens.closeBlock(line):
                depth -= 1
            if depth == 0: break
            block += line + ";\n"
        else:
            self._error(eofWarning.format(f'parsing block {blockName}'))
        return QASMBlock(self.currentFile, startline, block)

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class CBlock(CodeBlock):
    def __init__(self, block):
        CodeBlock.__init__(self,block)
        
class PyBlock(CodeBlock):
    def __init__(self, block):
        CodeBlock.__init__(self,block)

class IfBlock(CodeBlock):
    def __init__(self, cond, block):
        self._cond = cond
        CodeBlock.__init__(self, block)

class Gate(CodeBlock):

    gates = {}
    internalGates = {}

    def __init__(self, name, cargs, qargs, block, recursive = False, opaque = False):
        self.name = name
        if recursive: Gate.gates[self.name] = "Temp"
        if opaque and len(block) == 0 : block.File = [';']
        CodeBlock.__init__(self,block)
        if qargs:
            for qarg in qargs.split(','):
                self._qargs[qarg] = Argument(qarg, False)

        if cargs:
            for carg in cargs.split(','):
                self._cargs[carg] = Argument(carg, True)

        self._argNames = [arg.name for arg in list(self._qargs.values()) + list(self._cargs.values())]
        self.parse_instructions()
        Gate.gates[self.name] = self

    def new_variable(self, argument):
        if not argument.classical: raise IOError('Cannot declare new qarg in gate')
        else : raise IOError('Cannot declare new carg in gate')

    def parse_qarg_string(self, qargString):
        qargs = [ coreTokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        qargs = [[self._qargs[arg[0]], arg[0]+"_index"] for arg in qargs]
        return qargs

class Loop(CodeBlock):
    def __init__(self, block, var, start, end, step = 1):
        CodeBlock.__init__(self,block)
        self.depth = 1
        self.var = var
        self.start = start
        self.end = end
        if step != 1: raise NotImplementedError('Non contiguous loops not currently permitted')
        self.step = step
        self.parse_instructions()

class NestLoop(Loop):
    def __init__(self, block, var, start, end, step = 1):
        self._code = [block]
        self.depth = 1
        self.var = var
        self.start = start
        self.end = end
        if step != 1: raise NotImplementedError('Non contiguous loops not currently permitted')
        self.step = step
                    
