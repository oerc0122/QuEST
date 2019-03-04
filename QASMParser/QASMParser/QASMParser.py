from importlib import import_module
import copy

from .QASMTokens import *
from .QASMTypes import *
from .FileHandle import *
from .QASMErrors import *


class ProgFile(CodeBlock):
    def __init__(self, filename):
        self.filename = filename
        CodeBlock.__init__(self, QASMFile(filename), parent = None, copyFuncs = False, copyObjs = False)
        for gate in Gate.internalGates.values():
            self._funcs[gate.name] = gate
            self._objs[gate.name] = gate
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
            for obj in other._objs:
                if obj in self._objs:
                    print(obj)
                    self._error(includeWarning.format(name = obj, type = self._objs[obj].type_, other = other.filename, me = self.filename))
            for qarg in other._qargs:
                if qarg in self._qargs:
                    self._error(includeWarning.format(name = obj, type = self._objs[obj].type_, other = other.filename, me = self.filename))
                else:
                    self._qargs[qarg]  = other._qargs[qarg]
            for carg in other._cargs:
                if carg in self._cargs:
                    self._error(includeWarning.format(name = obj, type = self._objs[obj].type_, other = other.filename, me = self.filename))
                else:
                    self._cargs[carg]  = other._cargs[carg]
            for func in other._funcs:
                if func in Gate.internalGates: continue
                if func in self._funcs:
                    self._error(includeWarning.format(name = obj, type = self._objs[obj].type_, other = other.filename, me = self.filename))
                else:
                    self._funcs[func]  = other._funcs[func]
        else:
            raise TypeError(f'Cannot combine {type(self).__name__} with {type(other).__name__}')
