import re

class Token:

    def __init__(self, name: str, pattern: str):
        self.name = name
        self.re = re.compile(pattern.replace(' ','\s*'), re.I + re.X)
        self.string = pattern
        self.notOpenQASM = False
        
    def __str__(self):
        return self.string

    def __call__(self, string):
        return self.re.match(string)
    

class TokenSet(dict):
    
    def __init__(self):
        self._hlevel = {}

    def add(self, token: Token, hlevel = False, OpenQASMExtension = False):
        if token not in self.__dict__: self.__dict__[token.name] = token
        else: raise IOError(f'Token {token.name} already in tokenSet')
        if hlevel : self._hlevel[token.name] = token
        if OpenQASMExtension: token.notOpenQASM = True

tokens = TokenSet()

# Base Types
tokens.add(Token('blank', '^\s*$'))
tokens.add(Token('int', '\d+(?:[eE]+?\d+)?'))
tokens.add(Token('float', '[+-]?(?:\d*\.)?\d+(?:[eE][+-]?\d+)?'))
tokens.add(Token('compOp', '(?:<|>|==|!=)'))
tokens.add(Token('compJoin', '(?:&&|\|\|)'))
tokens.add(Token('mathOp', '[-+*/^]'))
tokens.add(Token('funcOp', '(?:sin|cos|tan|exp|ln|sqrt)'))
tokens.add(Token('validName', '[a-z]\w*'))
tokens.add(Token('openBlock', '\{'),True)
tokens.add(Token('closeBlock', '\}'),True)

tokens.add(Token('validSingRef', f'(?:(?:{tokens.int})|(?:{tokens.validName}))'))
tokens.add(Token('validRef', r'(?:{}(?:\:{})?)'.format(tokens.validSingRef, tokens.validSingRef)))

tokens.add(Token('qubitRef', '(?:\[{}\])'.format(tokens.validRef)))
tokens.add(Token('namedQubitRef', '(?:\[(?P<qubitIndex>{})\])'.format(tokens.validRef)))
tokens.add(Token('namedBitRef', '(?:\[(?P<bitIndex> {})\])'.format(tokens.validRef)))
tokens.add(Token('namedQarg', '(?P<qargName>{})'.format(tokens.validName)))
tokens.add(Token('namedCarg', '(?P<cargName>{})'.format(tokens.validName)))

tokens.add(Token('qarg', '{} {}?'.format(tokens.validName,tokens.qubitRef)))
tokens.add(Token('singCarg', '(?:{}|{}|{}{}?)'.format(tokens.float,tokens.int,tokens.validName,tokens.qubitRef)))
tokens.add(Token('cargOp', '{}(?: {} {})*'.format(tokens.singCarg,tokens.mathOp,tokens.singCarg)))
tokens.add(Token('funcCarg', '(?:(?:{}\({}\))|(?:{}))'.format(tokens.funcOp,tokens.cargOp, tokens.cargOp)))
tokens.add(Token('carg', '{}(?: {} {})*'.format(tokens.funcCarg, tokens.mathOp, tokens.funcCarg)))

tokens.add(Token('funcName', '(?P<funcName>{})'.format(tokens.validName)))
tokens.add(Token('namedQubit', '{} {}?'.format(tokens.namedQarg,tokens.namedQubitRef)))
tokens.add(Token('namedParam', '{} {}?'.format(tokens.namedCarg,tokens.namedBitRef)))

tokens.add(Token('singCond','{} {} {}'.format(tokens.carg,tokens.compOp,tokens.carg)))
tokens.add(Token('conditional','{}(?: {} {})*'.format(tokens.singCond,tokens.compJoin,tokens.singCond)))

tokens.add(Token('qargList', '(?P<qargs>{} (?:, {})*)'.format(tokens.qarg,tokens.qarg)))
tokens.add(Token('cargList', '(?:\((?P<cargs>{} (?:, {})*)\))'.format(tokens.carg,tokens.carg)))

tokens.add(Token('comment', '//(?P<comment>.*)$'))
tokens.add(Token('createReg', '(?P<regType>[qc])reg\s+{}'.format(tokens.namedQubit)), True)
tokens.add(Token('measure', 'measure\s+{}? -> {}'.format(tokens.namedQubit,tokens.namedParam)), True)
tokens.add(Token('wholeLineComment','^ //(?P<comment>.*)'), True)
tokens.add(Token('version', '(?P<Version>[a-zA-Z]+QASM)\s+(?P<majorVer>\d+)\.(?P<minorVer>\d+)'), True)
tokens.add(Token('include', 'include\s+[\'"](?P<filename>(?:\w|[./])+)[\'"]'), True)
tokens.add(Token('forLoop', 'for\s+(?P<var>{})\s+in\s+\[(?P<range>{})\] do'.format(tokens.validName, tokens.validRef)),True,True)
tokens.add(Token('reset', 'reset\s+{}'.format(tokens.namedQubit)), True)
tokens.add(Token('barrier', 'barrier\s+{}'.format(tokens.qargList)), True)
tokens.add(Token('gate', '{} {}?\s+{}'.format(tokens.funcName,tokens.cargList,tokens.qargList)))
tokens.add(Token('opaque', 'opaque\s+{}'.format(tokens.gate)), True)
tokens.add(Token('createRGate', 'rgate\s+{}'.format(tokens.gate)), True, True)
tokens.add(Token('createGate', 'gate\s+{}'.format(tokens.gate)), True)
tokens.add(Token('callGate', tokens.gate.string), True)
tokens.add(Token('CBlock', 'CBLOCK'), True, True)
tokens.add(Token('qop', re.sub(r'\(\?P\<[a-zA-Z]+\>','(','(?:{}|{}|{}|{})'.format(tokens.gate,tokens.createReg,tokens.include,tokens.measure))))

tokens.add(Token('ifLine','if \((?P<cond>{cond})\)(?P<op> {op})?'.format(cond=tokens.conditional,op=tokens.qop)), True)
tokens.add(Token('line',
                 '(?:(?:{ifLine})|(?:{newGate})|(?:{qop})|(?:{ver})); (?:{comm})?'.format(
                     ifLine = tokens.ifLine,
                     newGate= tokens.createGate,
                     qop = tokens.qop,
                     ver = tokens.version,
                     comm = tokens.comment)))
