from .QASMParser import *
# def __init__(self, filename, noFile = False):
# def __init__(self, name, cargs, qargs, block, QuESTGate = False, internalName = None):
# def __init__(self, parentName, startline, block):

class QuESTLibGate(Gate):
    def __init__(self, name, cargs, qargs, argOrder, internalName):
        self.name = name
        self._cargs = cargs
        self._qargs = self.parse_qargs_string(qargs)
        self.internalName = internalName
        self.argOrder = argOrder

    def reorder_args(self):
        
        
    def to_c(self):

        

QuESTLibGate(name = "x", cargs = None, qargs = "x", block = QASMBlock("QuESTInternal", 1, "// Internal"), QuESTGate = True, internalName = "pauliX")
QuESTLibGate(name = "cx", cargs = None, qargs = "x", block = QASMBlock("QuESTInternal", 1, "// Internal"), QuESTGate = True, internalName = "controlledNot")
QuESTLibGate(name = "ccx", cargs = None, qargs = "x", block = QASMBlock("QuESTInternal", 1, "// Internal"), QuESTGate = True, internalName = "multiControlledNot")
