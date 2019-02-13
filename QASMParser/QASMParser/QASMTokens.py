import re

class Token:

    def __init__(self, name: str, pattern: str):
        self.name = name
        self.re = re.compile(pattern, re.I + re.X)
        self.string = pattern

    def __str__(self):
        return self.string

    def __call__(self, string):
        return self.re.match(string)
    

class TokenSet(dict):
    
    def __init__(self):
        self._hlevel = {}

    def add(self, token: Token, hlevel = False):
        if token not in self.__dict__: self.__dict__[token.name] = token
        else: raise IOError(f'Token {token.name} already in tokenSet')
        if hlevel : self._hlevel[token.name] = token

tokens = TokenSet()

# Base Types
tokens.add(Token('blank', '^\s*$'))
tokens.add(Token('int', '\d+(?:[eE]+?\d+)?'))
tokens.add(Token('float', '[+-]?(?:\d*\.)?\d+(?:[eE][+-]?\d+)?'))
tokens.add(Token('compOp', '(?:<|>|==|!=)'))
tokens.add(Token('compJoin', '(?:&&|\|\|)'))
tokens.add(Token('mathOp', '[-+*/^|]'))
tokens.add(Token('validName', '[a-z]\w*'))
tokens.add(Token('openBlock', '\s*\{'), True)
tokens.add(Token('closeBlock', '\s*\}'), True)
tokens.add(Token('validRef', f'(?:(?:{tokens.int})|(?:{tokens.validName}))'))

tokens.add(Token('qubitRef', '(?:\[{}\])'.format(tokens.validRef)))
tokens.add(Token('namedQubitRef', '(?:\[(?P<qubitIndex>{})\])'.format(tokens.validRef)))
tokens.add(Token('namedBitRef', '(?:\[(?P<bitIndex> {})\])'.format(tokens.validRef)))
tokens.add(Token('namedQarg', '(?P<qargName>{})'.format(tokens.validName)))
tokens.add(Token('namedCarg', '(?P<cargName>{})'.format(tokens.validName)))

tokens.add(Token('qarg', '{}\s*{}?'.format(tokens.validName,tokens.qubitRef)))
tokens.add(Token('singCarg', '(?:{}|{}|{})'.format(tokens.float,tokens.int,tokens.validName)))
tokens.add(Token('carg', '{}(?:\s*{}\s*{})*'.format(tokens.singCarg,tokens.mathOp,tokens.singCarg)))
tokens.add(Token('funcName', '(?P<funcName>{})'.format(tokens.validName)))
tokens.add(Token('namedQubit', '{}\s*{}?'.format(tokens.namedQarg,tokens.namedQubitRef)))
tokens.add(Token('namedParam', '{}\s*{}?'.format(tokens.namedCarg,tokens.namedBitRef)))

tokens.add(Token('singCond','{}\s*{}\s*{}'.format(tokens.carg,tokens.compOp,tokens.carg)))
tokens.add(Token('conditional','{}(?:\s*{}\s*{})*'.format(tokens.singCond,tokens.compJoin,tokens.singCond)))

tokens.add(Token('qargList', '(?P<qargs>{}\s*(?:,\s*{})*)'.format(tokens.qarg,tokens.qarg)))
tokens.add(Token('cargList', '(?:\((?P<cargs>{}\s*(?:,\s*{})*)\))'.format(tokens.carg,tokens.carg)))

tokens.add(Token('comment', '//(?P<comment>.*)$'))
tokens.add(Token('createReg', '(?P<regType>[qc])reg\s+{}'.format(tokens.namedQubit)), True)
tokens.add(Token('measure', 'measure\s+{}\s*->\s*{}'.format(tokens.namedQubit,tokens.namedParam)), True)
tokens.add(Token('wholeLineComment','^\s*//(?P<comment>.*)'), True)
tokens.add(Token('version', 'OPENQASM\s+(?P<majorVer>\d+)\.(?P<minorVer>\d+)'), True)
tokens.add(Token('include', 'include\s+[\'"](?P<filename>(?:\w|[./])+)[\'"]'), True)
tokens.add(Token('gate', '{}\s*{}?\s+{}'.format(tokens.funcName,tokens.cargList,tokens.qargList)))
tokens.add(Token('createGate', 'gate\s+{}'.format(tokens.gate)), True)
tokens.add(Token('callGate', tokens.gate.string), True)
tokens.add(Token('qop', re.sub(r'\(\?P\<[a-zA-Z]+\>','(','(?:{}|{}|{}|{})'.format(tokens.gate,tokens.createReg,tokens.include,tokens.measure))))

tokens.add(Token('ifLine','if\s*\({cond}\)\s*{op}'.format(cond=tokens.conditional,op=tokens.qop)))
tokens.add(Token('line',
                 '(?:(?:{ifLine})|(?:{newGate})|(?:{qop})|(?:{ver}));\s*(?:{comm})?'.format(
                     ifLine = tokens.ifLine,
                     newGate= tokens.createGate,
                     qop = tokens.qop,
                     ver = tokens.version,
                     comm = tokens.comment)))
