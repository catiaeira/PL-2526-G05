import ply.lex as lex

# Análise Léxica
# . Implementar um analisador léxico (lexer) para converter código Fortran numa lista de tokens;
# . Usar a ferramenta ply.lex, na implementação do analisador léxico;
# . Identificar palavras-chave ( PROGRAM, INTEGER, REAL, LOGICAL, IF, DO, GOTO, etc.), identificadores,
# números, operadores e símbolos especiais.
# Nota: O grupo deve decidir se suportará o formato de colunas fixas do Fortran 77 ou o formato
# livre (free-form) das versões mais modernas.

# com colunas fixas

keywords = [
            'ASSIGN', 'BACKSPACE', 'BLOCKDATA', 'CALL', 'CLOSE', 
            'COMMON', 'CONTINUE', 'DATA', 'DIMENSION', 
            'DO', 'ELSE', 'ELSEIF', 'END', 'ENDFILE', 'ENDIF', 
            'ENTRY', 'EQUIVALENCE', 'EXTERNAL', 'FORMAT', 'FUNCTION', 
            'GOTO', 'IF', 'IMPLICIT', 'INQUIRE', 'INTRINSIC', 'OPEN', 
            'PARAMETER', 'PAUSE', 'PRINT', 'PROGRAM', 'READ', 'RETURN', 
            'REWIND', 'REWRITE', 'SAVE', 'STOP', 'SUBROUTINE', 'THEN', 
            'WRITE', 'INTEGER', 'REAL', 'CHARACTER', 'COMPLEX', 'LOGICAL', 
            'DOUBLEPRECISION'
            ]
tokens = [
        'ID', 'INT_LITERAL', 'REAL_LITERAL', 'DOUBLE_LITERAL', 'STRING_LITERAL', 'HOLLERITH',
        'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
        'AND', 'OR', 'NOT', 'EQV', 'NEQV', 'TRUE', 'FALSE',
        'POWER','CONCAT',
        'NEWLINE', 'CONTINUATION', 'LABEL'
        ] + keywords

literals = ['(', ')', ',', ':', '+', '-', '*', '/', '=']

states = (
    ('stmt', 'exclusive'),
)

# INITIAL state rules (cols 1-6)
# starts with C, c, *, or ! in column 1
def t_COMMENT(t):
    r'[Cc\*!][^\n]*'
    pass 

# no labels, transition to statement
def t_INITIAL_spaces(t):
    r'[ ]{6}'
    t.lexer.begin('stmt')

# label in columns 1-5, then column 6, then statement
def t_INITIAL_LABEL(t):
    r'[ ]{0,4}\d{1,5}[ ]'
    t.lexer.begin('stmt')
    t.value = int(t.value.strip())
    t.type = 'LABEL'
    return t

# continuation field
def t_INITIAL_continuation(t):
    r'[ ]{5}[^ 0\n]'
    t.lexer.begin('stmt')

def t_INITIAL_newline(t):
    r'\n'
    t.lexer.lineno += 1

def t_INITIAL_skip(t):
    r'[ \t]+'
    pass

def t_INITIAL_error(t):
    print(f"Illegal character in columns 1-6: '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)


# STATEMENT state rules (cols 7+)
# return to INITIAL
def t_stmt_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.begin('INITIAL')
    return t

def t_stmt_INLINE_COMMENT(t):
    r'![^\n]*'
    pass

t_stmt_POWER = r'\*\*'
t_stmt_CONCAT = r'//'

def t_stmt_EQ(t):
    r'\.EQ\.'
    return t

def t_stmt_NE(t):
    r'\.NE\.'
    return t

def t_stmt_LE(t):
    r'\.LE\.'
    return t

def t_stmt_LT(t):
    r'\.LT\.'
    return t

def t_stmt_GE(t):
    r'\.GE\.'
    return t

def t_stmt_GT(t):
    r'\.GT\.'
    return t

def t_stmt_AND(t):
    r'\.AND\.'
    return t

def t_stmt_OR(t):
    r'\.OR\.'
    return t

def t_stmt_NOT(t):
    r'\.NOT\.'
    return t

def t_stmt_EQV(t):
    r'\.EQV\.'
    return t

def t_stmt_NEQV(t):
    r'\.NEQV\.'
    return t

def t_stmt_TRUE(t):
    r'\.TRUE\.'
    t.value = True
    return t

def t_stmt_FALSE(t):
    r'\.FALSE\.'
    t.value = False
    return t

# D exponent
def t_stmt_DOUBLE_LITERAL(t):
    r'(\d+\.\d*|\.\d+|\d+)[Dd][+-]?\d+'
    t.value = float(t.value.replace('D', 'E').replace('d', 'e'))
    return t

# decimal point or E exponent
def t_stmt_REAL_LITERAL(t):
    r'(\d+\.\d*|\.\d+)([Ee][+-]?\d+)?|\d+[Ee][+-]?\d+'
    t.value = float(t.value)
    return t

def t_stmt_INT_LITERAL(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_stmt_STRING_LITERAL(t):
    r"'([^']|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t

# nH followed by n characters: 3HBYE -> BYE
def t_stmt_HOLLERITH(t):
    r'\d+[Hh]'
    count = int(t.value[:-1])
    start = t.lexer.lexpos
    t.value = t.lexer.lexdata[start:start + count]
    t.lexer.lexpos += count
    return t

def t_stmt_ID(t):
    r'[A-Za-z][A-Za-z0-9]*'
    upper = t.value.upper()
    if upper in keywords:
        t.type = upper
        t.value = upper
    else:
        t.value = upper
    return t

t_stmt_ignore = ' \t'

def t_stmt_literal(t):
    r'[(),:\+\-\*/=]'
    t.type = t.value
    return t

def t_stmt_error(t):
    print(f"Illegal character: '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()

def main():
    test_code = '''
C     This is a comment
      PROGRAM HELLO
      INTEGER I, J
      REAL X
      DOUBLE PRECISION Y
      CHARACTER*10 NAME ! comment
      
      X = 3.14
      Y = 2.718D0
      I = 42
      NAME = 'WORLD'
      
      DO 10 I = 1, 10
        IF (I .GT. 5) THEN
          PRINT *, 'BIG'
        ELSE
          PRINT *, 'SMALL'
        ENDIF
   10 CONTINUE
      
      STOP
      END
'''
    lexer.input(test_code)
    
    for tok in lexer:
        print(tok)

if __name__ == '__main__':
    main()