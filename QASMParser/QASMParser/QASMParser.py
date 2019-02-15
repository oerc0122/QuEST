import copy

from .QASMTokens import *
from .langs.Base import *
from .FileHandle import *
# Declare several warnings which may occur
argWarning  = 'Bad argument list in {} expected {}, recieved {}'
existWarning  = '{Type} {Name} has not been declared'
eofWarning = 'Unexpected end of file while {}'
dupWarning = '{Type} {Name} is already declared'
fileWarning = '{message} in {file} at line {line}'
fnfWarning  = 'File {} not found'
typeWarning = 'Unrecognised type {} requested in function {}'
indexWarning = "Index {Req} out of range for {Var}, max index {Max}"
argSizeWarning = "Args {Var} and {Var2} are different sizes and cannot be implicitly assigned.\n" + indexWarning
includeNotMainWarning = "Cannot include files in block {}"

class ProgFile(CodeBlock):
    def __init__(self, filename):
        self.filename = filename
        CodeBlock.__init__(self,QASMFile(filename))
        self._funcs= copy.copy(Gate.internalGates)
        self.parse_instructions()
        
    def to_lang(self, filename = None):
        if filename:
            with open(filename, 'w') as outputFile:
                for line in self._code:
                    outputFile.write(line.to_lang() + "\n")
        else:
            for line in self._code:
                print(line.to_lang())
    
    def run(self):
        for line in self._code:
            exec(line.to_python())

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



