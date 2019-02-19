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
QASMWarning = "Unrecognised QASM Version statement {}"
instructionWarning = "Unrecognised instruction: {} not in {} format"
langWarning = "QASM instruction {} not implemented in output language."
langNotDefWarning = "Language {0} translation not found, check QASMParser/langs/{0}.py exists."
