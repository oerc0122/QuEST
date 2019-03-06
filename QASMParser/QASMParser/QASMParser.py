from importlib import import_module
import sys
import os.path
from .QASMTokens import *
from .QASMTypes import *
from .FileHandle import *
from .QASMErrors import *


class ProgFile(CodeBlock):
    def __init__(self, filename):
        self.filename = filename
        CodeBlock.__init__(self, QASMFile(filename), parent = None, copyFuncs = False, copyObjs = False)
        for gate in Gate.internalGates.values():
            self._objs[gate.name] = gate
        self.parse_instructions()
        
    def to_lang(self, filename = None, module = False, lang = "C", verbose = False):
        try:
            lang = import_module(f"QASMParser.langs.{lang}")
            lang.set_lang()
        except ImportError:
            raise NotImplementedError(langNotDefWarning.format(lang))

        indent = lang.indent
        writeln = lambda toWrite: outputFile.write(self.depth*indent + toWrite + "\n")

        def print_code(self, code, outputFile):
            self.depth += 1
            for line in code:
                # Verbose -- Print original
                if verbose and hasattr(line,'original') and type(line) is not Comment:
                    outputFile.write(self.depth*indent + Comment(line.original).to_lang() + "\n")
                # Handle loops
                if hasattr(line,"_loops") and line._loops:
                    writeln(line._loops.to_lang() + lang.blockOpen)
                    print_code(self,line._loops._code,outputFile)
                    writeln(lang.blockClose)
                # Print children
                elif hasattr(line,"_code") and type(line) not in [CBlock, PyBlock]:
                    writeln(line.to_lang() + lang.blockOpen)
                    print_code(self,line._code,outputFile)
                    writeln(lang.blockClose)
                # Print self
                else:
                    writeln(line.to_lang())
                
            self.depth -= 1
            
        if filename: outputFile = open(filename, 'w')
        else:        outputFile = sys.stdout

        codeToWrite = copy.copy(self._code)
        self.depth = -1
       
        for line in self.currentFile.header:
            writeln(line)
        if hasattr(lang,'include'):
            writeln(lang.include('QuEST.h'))
            
        if lang.hoistFuncs:
            codeToWrite = sorted(self._code, key = lambda x: type(x).__name__ == "Gate")
            while type(codeToWrite[-1]) is Gate:
                gate = [codeToWrite.pop()]
                print_code(self, gate, outputFile)
        if module:
            if filename: funcName = os.path.splitext(os.path.basename(filename))[0]
            else:        funcName = "module"
        else:
            funcName = "main"
            
        if not lang.bareCode:
            temp = Gate(self, funcName, "", "", NullBlock(self.currentFile))
            temp._code = [InitEnv()]
            # Hoist qregs
            regs = [ x for x in codeToWrite if type(x).__name__ == "QuantumRegister" ]
            for reg in regs:
                temp._code += [Comment(f'{reg.name}[{reg.start}:{reg.end-1}]')]
            codeToWrite = [ x for x in codeToWrite if type(x).__name__ != "QuantumRegister" ]
            temp._code += [QuantumRegister("qreg", QuantumRegister.numQubits)]
            temp._code += codeToWrite
            codeToWrite = [temp]
        print_code(self, codeToWrite, outputFile)
            
        if filename: outputFile.close()
        
    def run(self):
        try:
            lang = import_module(f"QASMParser.langs.Python")
            lang.set_lang()
        except ImportError:
            raise NotImplementedError(langNotDefWarning.format(lang))

        for line in self._code:
            exec(line.to_lang())

    def include(self, filename):
        other = ProgFile(filename)
        if isinstance(other, ProgFile):
            self._code += other._code
            for obj in other._objs:
                if obj in Gate.internalGates: continue
                if obj in self._objs:
                    self._error(includeWarning.format(
                        name = obj, type = self._objs[obj].type_, other = other.filename, me = self.filename)
                    )
                else:
                    self._objs[obj] = other._objs[obj]
        else:
            raise TypeError(f'Cannot combine {type(self).__name__} with {type(other).__name__}')
