import copy

from .QASMTokens import *
from .QASMTypes import *
from .FileHandle import *
from importlib import import_module
from .QASMErrors import *


class ProgFile(CodeBlock):
    def __init__(self, filename):
        self.filename = filename
        CodeBlock.__init__(self,QASMFile(filename))
        self._funcs= copy.copy(Gate.internalGates)
        self.parse_instructions()
        
    def to_lang(self, filename = None, lang = "C"):
        try:
            lang = import_module(f"QASMParser.langs.{lang}")
            lang.set_lang()
        except ImportError:
            raise NotImplementedError(langNotDefWarning.format(lang))
            
        if filename:
            with open(filename, 'w') as outputFile:
                for line in self._code:
                    outputFile.write(line.to_lang() + "\n")
        else:
            for line in self._code:
                print(line.to_lang())
    
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
