from .QASMErrors import *
from .QASMTokens import *
from .FileHandle import QASMFile, QASMBlock, NullBlock
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
            self.innermost = NestLoop(copy.copy(self), index, start, end)
            self._loops = self.innermost

    def finalise_loops(self):
        if self._loops:
            self.innermost._code = [copy.copy(self)]
            self.innermost._code[0]._loops = []
        else:
            pass
            
    def handle_loops(self, pargs, slice = None):
        for parg in pargs:
            parg[1] = parg[1]
            if parg[1] is None:
                parg[1] = parg[0].name + "_index"
                self.add_loop(parg[1], 1, parg[0].size)
                
            elif isinstance(parg[1], str):
                pargSplit = parg[1].split(':')
                if len(pargSplit) == 1: # Just index
                    if pargSplit[0].isdecimal():
                        parg[1] = int(pargSplit[0])
                    else: # Do nothing, assume the variable is fine
                        pass
                    
                elif len(pargSplit) == 2: # Min Max
                    parg[1] = parg[0].name + "_index"
                    pargMin = 1
                    pargMax = parg[0].size
                    if pargSplit[0]: pargMin = int(pargSplit[0])
                    if pargSplit[1]: pargMax = int(pargSplit[1])
                    self.add_loop(parg[1], pargMin, pargMax)
                    
                else: raise IOError('Bad Index syntax')
                
    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))
                
class Comment:
    def __init__(self, comment):
        self.name = comment
        self.comment = comment

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class Referencable:
    def __init__(self):
        self.type_ = type(self).__name__
    
class Constant(Referencable):
    def __init__(self, name, val):
        Referencable.__init__(self)
        self.name = name
        self.val  = val

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class Register(Referencable):
    def __init__(self, name, size):
        Referencable.__init__(self)
        self.name = name
        self.size = int(size)

    def __repr__(self):
        return f"{self.name}[{self.size}]"

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))
    
class QuantumRegister(Register):
    pass

class ClassicalRegister(Register):
    pass
    
class Argument(Referencable):
    def __init__(self, name, classical):
        Referencable.__init__(self)
        self.name = name
        self.classical = classical

    def __repr__(self):
        if classical: return self.name
        else: return self.name

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class Let:
    def __init__(self, var, val):
        self.var = var
        self.val = val

    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class CallGate(VarHandler):
    def __init__(self, gate, cargs, qargs):
        self.name = gate
        VarHandler.__init__(self, qargs, cargs)
        self.handle_loops(self._qargs)
        if cargs: self._cargs = cargs.split(',')
        else: self._cargs = []

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
        # Check bindices
        if bindex is None:
            if carg.size < qarg.size:
                raise IOError(argSizeWarning.format(Req=qarg.size, Var=carg.name, Var2 = qarg.name, Max=carg.size))
            if carg.size > qarg.size:
                raise IOError(argSizeWarning.format(Req=carg.size, Var=qarg.name, Var2 = carg.name, Max=qarg.size))
            self._cargs[1] = self._qargs[1]

        self.carg = self._cargs[0]
        self.bindex = self._cargs[1]
        self.qarg = self._qargs[0]
        self.qindex = self._qargs[1]

        self.finalise_loops()
        
    def __repr__(self):
        return f"measure {self.qarg}[{self.qindex}] -> {self.carg}[{self.bindex}]"

class Reset(VarHandler):
    def __init__(self, qarg):
        VarHandler.__init__(self, qarg)
        self.handle_loops([self._qargs])

    def __repr__(self):
        return f"reset {self.qarg}[{self.qindex}]"

class EntryExit:
    def __init__(self, parent):
        self.parent = parent
        self.depth = 1

    def exited(self):
        self.depth = 0
        
    def to_lang(self):
        raise NotImplementedError(langWarning.format(type(self).__name__))

class CodeBlock:
    def __init__(self, block, parent, copyObjs = True, copyFuncs = True):
        self._code = []
        self._qargs= {}
        self._cargs= {}
        if copyObjs:
            self._objs = copy.copy(parent._objs)
        else:
            self._objs = {}
        if copyFuncs:
            self._funcs= copy.copy(parent._funcs)
        else:
            self._funcs = {}
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
        self._is_def(argName, create=True)

        if classical:
            variable = ClassicalRegister(argName, size)
            self._cargs[argName] = variable
            self._objs[argName] = variable
        else:
            variable = QuantumRegister(argName, size)
            self._qargs[argName] = variable
            self._objs[argName] = variable
            
        self._code += [variable]

    def gate(self, funcName, cargs, qargs, block, recursive = None, opaque = None):
        self._is_def(funcName, create=True)

        gate = Gate(self, funcName, cargs, qargs, block, recursive, opaque)
        self._funcs[gate.name] = gate
        self._objs[gate.name] = gate
        self._code += [gate]

    def let(self, var, val):
        self._is_def(var, create=True)
        self._objs[var] = Constant(var,val)
        self._code += [Let(var, val)]
        
    def call_gate(self, funcName, cargs, qargs):
        self._is_def(funcName, create=False, type_ = 'Gate')
        
        qargs = self.parse_qarg_string(qargs)
        # if funcName not in self._funcs: self._error(existWarning.format(Type = 'Gate', Name = funcName))
        gate = CallGate(funcName, cargs, qargs)
        self._code += [gate]

    def measurement(self, qarg, qindex, carg, bindex):
        self._is_def(carg, create=False, type_ = 'ClassicalRegister')
        self._is_def(qarg, create=False, type_ = 'QuantumRegister')
        carg = self._cargs[carg]
        qarg = self._qargs[qarg]
        if bindex:
            bindex = int(bindex)
            if bindex > carg.size - 1 or bindex < 0 :
                self._error(indexWarning.format(Var=carg,Req=bindex,Max=carg.size))

        if qindex:
            qindex = int(qindex)
            if qindex > qarg.size - 1 or qindex < 0 :
                self._error(indexWarning.format(Var=qarg,Req=qindex,Max=qarg.size))

        measure = Measure( [qarg, qindex], [carg, bindex] )
        
        self._code += [measure]

    def leave(self):
        if hasattr(self, "entry"):
            self.entry.exited()
        else:
            self._error('Cannot exit from a non-recursive gate')

    def reset(self, qarg, qindex):
        if qarg not in self._qargs : self._error(existWarning.format(Type = 'Qreg', Name = qarg))
        else : qarg = self._qargs[qarg]
        if qindex:
            qindex = int(qindex)
            if qindex > qarg.size - 1 or qindex < 0 :
                self._error(indexWarning.format(Var=qarg,Req=qindex,Max=qarg.size))

        reset = Reset( [qarg, qindex] )
        
        self._code += [reset]

    def loop(self, var, block, start, end):
        loop = Loop(block, var, start, end)
        self._code += [loop]
        
    def new_if(self, cond, block):
        self._code += [IfBlock(self, cond, block)]

    def cBlock(self, block):
        self._code += [CBlock(self, block)]

    def _resolve(self, var, index, type_, reason = ""):
        if type_ == "Index":
            if var.is_decimal():
                return int(var)
            self._is_def(var, create=False, type_ = "Index")
            return self._objs[var]
        
        elif type_ in ["ClassicalRegister","QuantumRegister"]:
            self._is_def(var, create=False, type_ = type_)
            # Add index checking?
            return self._objs[var]
        
        elif type_ == "Constant":
            self._is_def(var, create=False, type_ = type_)
            return self._objs[var]
        
        elif type_ == "Gate":
            self._is_def(var, create=False, type_ = type_)
            # Add argument checking?
            return self._objs[var]
        
    def _is_def(self, name, create, type_ = None):
        if create: # Check for duplicate naming
            if name in self._objs: self._error(dupWarning.format(Name=name, Type=self._objs[name].type_))
                                               
        else: # Check exists and type is right
            if name not in self._objs:
                self._error(existWarning.format(Type=type_, Name=name))
            elif type_ == "Index": # Special case for index vars
                if self._objs[name].type_ not in ['Constant', 'ClassicalRegister']:
                    self._error(wrongTypeWarning.format(self._objs[name].type_, type_))
            elif self._objs[name].type_ is not type_:
                self._error(wrongTypeWarning.format(self._objs[name].type_, type_))
            else: pass
                                                                
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
            self.reset(qarg, qindex)
        elif token.name == "forLoop":
            var = match.group('var')
            start, end = match.group('range').split(':')
            block = self.parse_block("for loop")
            self.loop(var, block, start, end)
        elif token.name == "let":
            var = match.group('var')
            val = match.group('val')
            self.let(var, val)
        elif token.name == "exit":
            self.leave()
        else:
            self._error(instructionWarning.format(line.lstrip().split()[0], self.currentFile.QASMType))
        self._code[-1].original = line
            
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
    def __init__(self, parent, block):
        CodeBlock.__init__(self,block, parent=parent)
        
class PyBlock(CodeBlock):
    def __init__(self, parent, block):
        CodeBlock.__init__(self,block, parent=parent)

class IfBlock(CodeBlock):
    def __init__(self, parent, cond, block):
        self._cond = cond
        CodeBlock.__init__(self, block, parent=parent)
        self.parse_instructions()
        
class Gate(Referencable, CodeBlock):

    gates = {}
    internalGates = {}

    def __init__(self, parent, name, cargs, qargs, block, recursive = False, opaque = False):
        Referencable.__init__(self)
        self.name = name
        if opaque and len(block) == 0 : block.File = [';']
        CodeBlock.__init__(self, block, parent=parent)
        if recursive:
            self.gate(name, cargs, qargs, NullBlock(block))
            self._code = []
            self.entry = EntryExit(self.name)
        
        if qargs:
            for qarg in qargs.split(','):
                self._qargs[qarg] = Argument(qarg, False)

        if cargs:
            for carg in cargs.split(','):
                self._cargs[carg] = Argument(carg, True)

        self._argNames = [arg.name for arg in list(self._qargs.values()) + list(self._cargs.values())]
        self.parse_instructions()
        Gate.gates[self.name] = self
        if recursive and self.entry.depth > 0: self._error(noExitWarning.format(self.name))
        
    def new_variable(self, argument):
        if not argument.classical: raise IOError('Cannot declare new qarg in gate')
        else : raise IOError('Cannot declare new carg in gate')

    def parse_qarg_string(self, qargString):
        qargs = [ coreTokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        qargs = [[self._qargs[arg[0]], arg[0]+"_index"] for arg in qargs]
        return qargs

class Loop(CodeBlock):
    def __init__(self, parent, block, var, start, end, step = 1):
        CodeBlock.__init__(self,block, parent=parent)
        self._pargs += [var]
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
                    
