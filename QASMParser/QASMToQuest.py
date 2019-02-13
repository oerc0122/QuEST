from QASMParser.QASMParser import *
import QASMParser.QASMQuESTGate
myProg = Prog('./test1.qasm')
myProg.to_c("test")
