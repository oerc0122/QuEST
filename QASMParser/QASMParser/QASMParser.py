import re
import os.path
import copy
from .QASMTokens import *
# Declare several warnings which may occur
argWarning  = 'Bad argument list in {0:s} expected {1:d}, recieved {2:d}'
argWarningGen  = 'Bad argument list in {} expected {}, recieved {}'
existWarning  = '{Type} {Name} has not been declared'
eofWarning = 'Unexpected end of file while {}'
dupWarning = '{Type} {Name} is already declared'
fileWarning = '{message} in {file} at line {line}'
fnfWarning  = 'File {} not found'
typeWarning = 'Unrecognised type {} requested in function {}'


class QASMFile:

    _QASMFiles = []

    def __init__(self,filename, reqVersion=("2","0")):
        if filename in QASMFile._QASMFiles: raise IOError('Circular dependency in includes')
        if os.path.isfile(filename): self.File = open(filename,'r')
        else: raise FileNotFoundError()
        self.path = filename
        self.name = filename[filename.rfind('/')+1:] # Remove path
        QASMFile._QASMFiles.append(self.name)
        self.nLine = 0
        temp = ''
        self.header = ''
        try:
            line=self.readline()
            while line is not None:
                if tokens.wholeLineComment(line):
                    self.header += line
                elif tokens.version(line):
                    self.version = tokens.version(line).group(1,2)
                    break
                else:
                    self._error('Header of file :\n'+temp+"\n does not contain version")
                line=self.readline()

            if reqVersion[0] > self.version[0] :
                self._error('Unsupported QASM version: {}.{}'.format(*self.version))
        except AttributeError:
            self._error("Header does not contain version")
        except RuntimeError:
            self._error(eofWarning.format('trying to determine QASM version'))

    def _error(self, message=""):
        raise IOError(fileWarning.format(message=message,
                                         file=self.name, line=self.nLine))

    def __del__(self):
        try:
            openFiles = QASMFile._QASMFiles
            del openFiles[openFiles.index(self.name)]
            self.File.close()
        except AttributeError:
            return

    def block_split(self, line):
        match = re.findall('(@|\{|\}|[^{}@]+)', line)
        return [inst for inst in match if not re.match('^\s+$',inst)]
    def read_instruction(self):
        line = self.readline()
        lines = ""
        depth = 0
        while line is not None:
            lines += line.rstrip('\n')
            if tokens.wholeLineComment(lines):
                yield lines
                lines = ""

            *tmpInstructions, lines = lines.split(';')
            if len(tmpInstructions) > 0:
                instructions = []
                for instruction in tmpInstructions:
                    instructions += self.block_split(instruction)
                while instructions:
                    currInstruction = instructions.pop(0).strip()
                    yield currInstruction
            line = self.readline()


    def readline(self):
        """ Reads a line from a file """
        for line in self.File:
            self.nLine += 1
            if tokens.blank(line): continue
            return line
        else:
            return None

class QASMBlock(QASMFile):
    def __init__(self, parentName, startline, block):
        self.name = parentName
        self.File = block.splitlines()
        self.nLine = startline

    def readline(self):
        """ Reads a line from a file """
        while len(self.File) > 0:
            line = self.File.pop(0)
            self.nLine += 1
            if tokens.blank(line): continue
            return line
        else:
            return None

    def __del__(self):
        del self

class Comment:
    def __init__(self, comment : str):
        self.comment = comment

    def to_c(self):
        return "//" + self.comment

    def to_python(self):
        return "#" + self.comment

class Variable:
    def __init__(self, name : str, size : int, classical : bool):
        self.name = name
        self.size = size
        self.classical = classical

    def to_c(self):
        if self.classical: return f'int[{self.size}] {self.name};'
        else: return f"Qureg {self.name} = createQureg({self.size}, Env);"

    def to_python(self):
        if self.classical: return f'{self.name} = [0]*{self.size}'
        else: f'{self.name} = createQureg({self.size}, Env)'

class Argument:
    def __init__(self, name, classical):
        self.name = name
        self.classical = classical

    def to_c(self):
        if self.classical: return f'qreal {self.name}'
        else: return f'Qureg {self.name}, int {self.name}_index'

    def to_python(self):
        return self.name

class CallGate:
    def __init__(self, gate, cargs, qargs):
        self.gate = gate
        self._loops = []
        self._qargs = qargs
        for qarg in self._qargs:
            if qarg[1] is None:
                qarg[1] = qarg[0].name + "_index"
                self._loops.append((qarg[1], qarg[0].size))
        if cargs: self._cargs = cargs.split(',')
        else: self._cargs = []
    def to_c(self):

        if self.gate in Gate.internalGates:
            gateRef   = Gate.internalGates[self.gate]
            preString, printArgs = gateRef.reorder_args(self._qargs,self._cargs)
            printGate = gateRef.internalName
        else:
            printArgs = ", ".join([f"{qarg[0].name}, {qarg[1]}" for qarg in self._qargs])
            for carg in self._cargs:
                printArgs += ", "+carg
            printGate = self.gate
            preString = []

        outString = ""
        indent = "  "
        depth = 0
        if self._loops:
            Cfor = "for (int {var} = {min}; {var} < {max}; {var} += {step}) {{\n"
            for loop in self._loops:
                outString += indent*depth + Cfor.format(var = loop[0], min = 0, max = loop[1], step = 1)
                depth += 1
            for line in preString:
                outString += indent*depth + line + ";\n"
            outString += f"{indent*depth+printGate}({printArgs}); \n"
            for loop in self._loops:
                depth -= 1
                outString += indent*depth + "}\n"
            return outString
        else:
            for line in preString:
                outString += indent*depth + line + ";\n"
            outString += f"{indent*depth+printGate}({printArgs});"
            return outString

    def to_python(self):
        if self._loops:
            return ""
        else:
            printArgs = ", ".join([f"{qarg[0].name}, {qarg[1]}" for qarg in self._qargs])
            for carg in self._cargs:
                printArgs += ", "+carg
            return f"{self.gate}({printArgs})"

class Measure:
    def __init__(self, qarg, qindex, carg, bindex):
        self.qarg = qarg
        self.qindex = qindex
        self.carg = carg
        self.bindex = bindex

    def to_c(self):
        return f"{self.carg}[{self.bindex}] = measure({self.qarg}, {self.qindex});"

    def to_python(self):
        return f"{self.carg}[{self.bindex}] = measure({self.qarg}, {self.qindex})"

class Prog:
    def __init__(self, filename):
        self._code = []
        self._qargs= {}
        self._cargs= {}
        self._funcs= copy.copy(Gate.internalGates)
        self.filename = filename
        self.currentFile = QASMFile(filename)
        self.instructions = self.currentFile.read_instruction()
        self.parse_instructions()
    def to_c(self, filename):
        with open(filename, 'w') as outputFile:
            for line in self._code:
                outputFile.write(line.to_c() + "\n")

    def to_python(self):
        for line in self._code:
            exec(line.to_python())

    def __add__(self, other):
        if isinstance(other, Prog):
            self._code += other._code
            for qarg in other._qargs:
                if qarg in self._qargs:
                    raise IOError('Symbol defined in {other.filename} already defined in {self.filename}')
                else:
                    self._qargs[qarg]  = other._qargs[qarg]
            for carg in other._cargs:
                if carg in self._cargs:
                    raise IOError('Symbol defined in {other.filename} already defined in {self.filename}')
                else:
                    self._cargs[carg]  = other._cargs[carg]
            for func in other._funcs:
                if func in Gate.internalGates: continue
                if func in self._funcs:
                    raise IOError('Symbol defined in {other.filename} already defined in {self.filename}')
                else:
                    self._funcs[func]  = other._funcs[func]
        else:
            raise TypeError(f'Cannot combine {type(self).__name__} with {type(other).__name__}')

    def comment(self, comment):
        self._code += [Comment(comment)]

    def new_variable(self, argName, size, classical):
        variable = Variable(argName, size, classical)
        if variable in self._cargs or variable in self._qargs or variable in self._funcs:
            raise OSError(dupWarning.format(Type = "Variable", Name = variable.name))
        self._code += [variable]
        if variable.classical: self._cargs[variable.name] = variable
        else:                  self._qargs[variable.name] = variable

    def gate(self, funcName, cargs, qargs, block):
        if funcName in self._funcs: raise self.currentFile._error(dupWarning.format('Gate', gate))
        gate = Gate(funcName, cargs, qargs, block)
        self._funcs[gate.name] = gate
        self._code += [gate]

    def call_gate(self, funcName, cargs, qargs):
        qargs = self.parse_qarg_string(qargs)
        if funcName not in self._funcs: self.currentFile._error(existWarning.format(Type = 'Gate', Name = funcName))
        gate = CallGate(funcName, cargs, qargs)
        self._code += [gate]

    def measurement(self, qarg, qindex, carg, bindex):
        measure = Measure(qarg, qindex, carg, bindex)
        self._code += [measure]

    def new_if(self, cond, block):
        self._code += [IfBlock(cond, block)]

    def cBlock(self, block):
        self._code += [CBlock(block)]

    def parse_line(self, line, token):
        match = token(line)
        if token.name == "include":
            self.__add__(Prog(match.group('filename')))
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
        else :
            self.currentFile._error('Unimplemented instruction' + line)
        
    def parse_qarg_string(self, qargString):
        qargs = [ tokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        for qarg in qargs:
            if qarg[0] not in self._qargs: raise self.currentFile.error()
        qargs = [[self._qargs[arg[0]], int(arg[1])] if arg[1] is not None and arg[1].isdecimal()
                 else [self._qargs[arg[0]], arg[1]]
                 for arg in qargs]
        return qargs

    def parse_instructions(self):
        for line in self.instructions:
            for name, token in tokens._hlevel.items():
                if token(line) is not None:
                    self.parse_line(line, token)
                    break
            else: self.currentFile._error('Invalid instruction: "'+line+'"')

    def parse_block(self, blockname):
        blockOpen = next(self.instructions)
        if tokens.openBlock(blockOpen):
            close = tokens.closeBlock
        elif tokens.openCBlock(blockOpen):
            close = tokens.closeCBlock
        else:
            self.currentFile._error(f'{blockname} specification not followed by open block')
        startline = self.currentFile.nLine
        block = ""
        for line in self.instructions:
            if close(line): break
            block += line + ";"
        else:
            self.currentFile._error(eofWarning.format(f'parsing block {blockName}'))
        return QASMBlock(self.currentFile.name, startline, block)

class CBlock(Prog):
    def __init__(self, block):
        self.currentFile = block
        self.instructions = self.currentFile.read_instruction()

    def to_c(self):
        outStr = ""
        for instruction in self.instructions:
            outStr += instruction+";\n"
        return outStr

class IfBlock(Prog):

    def __init__(self, cond, block):
        self._cond = cond
        self._code = []
        self.currentFile = block
        self.instructions = self.currentFile.read_instruction()
        self.parse_instructions()

    def to_c(self):
        outStr = f"if ({self._cond}) {{\n"
        for line in self._code:
            outStr += "  "+line.to_c()
        outStr += "}"
        return outStr

    def to_python(self):
        printArgs = ",".join([arg.to_python() for arg in self._qargs + self._cargs])
        outSTr = f"if ({self._cond}):"
        for line in self._code:
            outStr += "    "+line.to_python()
        return outStr


class Gate(Prog):

    gates = {}
    internalGates = {}

    def __init__(self, name, cargs, qargs, block):
        self.name = name
        self._code = []
        self._cargs = {}
        self._qargs = {}
        if qargs:
            for qarg in qargs.split(','):
                self._qargs[qarg] = Argument(qarg, False)

        if cargs:
            for carg in cargs.split(','):
                self._cargs[carg] = Argument(carg, True)


        self._argNames = [arg.name for arg in list(self._qargs.values()) + list(self._cargs.values())]
        self._funcs= Gate.gates
        self.currentFile = block
        self.instructions = block.read_instruction()
        self.parse_instructions()
        Gate.gates[self.name] = self

    def new_variable(self, argument):
        if not argument.classical: raise IOError('Cannot declare new qarg in gate')
        else : raise IOError('Cannot declare new carg in gate')

    def parse_qarg_string(self, qargString):
        qargs = [ tokens.namedQubit(qarg).groups() for qarg in qargString.split(',')]
        qargs = [[self._qargs[arg[0]], arg[0]+"_index"] for arg in qargs]
        return qargs

    def to_c(self):
        printArgs = ", ".join([f"{qarg}, {qarg}_index" for qarg in self._qargs])
        for carg in self._cargs:
            printArgs += ", "+carg
        outStr = f"void {self.name}({printArgs}) {{\n"
        for line in self._code:
            outStr += "  "+line.to_c() +"\n"
        outStr += "}"
        return outStr

    def to_python(self):
        printArgs = ",".join([arg.to_python() for arg in self._qargs + self._cargs])
        outSTr = f"def {self.name}({printArgs}):"
        for line in self._code:
            outStr += "    "+line.to_python()
        return outStr
