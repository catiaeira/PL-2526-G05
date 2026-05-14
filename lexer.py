import ply.lex as lex
import re as re

class LexError(Exception):
    pass

not_implemented_keywords =  {
    'ASSIGN': 'ASSIGN', 'BACKSPACE': 'BACKSPACE', 'BLOCKDATA': 'BLOCKDATA', 
    'CLOSE': 'CLOSE', 'COMMON': 'COMMON', 'DATA': 'DATA', 'ENDFILE': 'ENDFILE',
    'ENTRY': 'ENTRY', 'EXTERNAL': 'EXTERNAL', 'FORMAT': 'FORMAT', 'EQUIVALENCE': 'EQUIVALENCE',
    'IMPLICIT': 'IMPLICIT', 'INQUIRE': 'INQUIRE', 'INTRINSIC': 'INTRINSIC', 'OPEN': 'OPEN',
    'PAUSE': 'PAUSE', 'REWIND': 'REWIND', 'REWRITE': 'REWRITE', 'TO': 'TO', 'HOLLERITH' : 'HOLLERITH',
    'DIMENSION': 'DIMENSION'
}

keywords = {
    'CALL': 'CALL', 'CONTINUE': 'CONTINUE', 'DO': 'DO',
    'ELSE': 'ELSE', 'ELSEIF': 'ELSEIF', 'END': 'END',
    'ENDIF': 'ENDIF', 'FUNCTION': 'FUNCTION',
    'GOTO': 'GOTO', 'IF': 'IF', 'PARAMETER': 'PARAMETER',
    'PRINT': 'PRINT', 'PROGRAM': 'PROGRAM', 'READ': 'READ',
    'RETURN': 'RETURN', 'SAVE': 'SAVE', 'STOP': 'STOP', 
    'SUBROUTINE': 'SUBROUTINE', 'THEN': 'THEN',
    'WRITE': 'WRITE', 'INTEGER': 'INTEGER', 'REAL': 'REAL',
    'CHARACTER': 'CHARACTER', 'COMPLEX': 'COMPLEX',
    'LOGICAL': 'LOGICAL', 'DOUBLEPRECISION': 'DOUBLEPRECISION',
}

tokens = [
    'ID', 'INT_LITERAL', 'REAL_LITERAL', 'DOUBLE_LITERAL', 'STRING_LITERAL',
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'AND', 'OR', 'NOT', 'EQV', 'NEQV',
    'TRUE', 'FALSE',
    'POWER', 'CONCAT',
    'NEWLINE', 'LABEL'
] + list(keywords.values())

literals = ['(', ')', ',', ':', '+', '-', '*', '/', '=']

states = (
    ('stmt', 'exclusive'),
)

class FortranLexer:
    tokens = tokens
    literals = literals
    states = states

    def __init__(self):
        self.lexer = lex.lex(module=self, reflags=re.MULTILINE)
        self.errors = []
        self.pending_newline = False

    def input(self, data):
        self.errors.clear()
        self.lexer.input(data)

    def token(self):
        return self.lexer.token()

    # ---------- INITIAL (cols 1–6) ----------

    def t_INITIAL_comment(self, t):
        r'^[Cc\*!].*'
        pass

    def t_INITIAL_blank(self, t):
        r'[ ]*\n'
        t.lexer.lineno += 1

    def t_INITIAL_start_line(self, t):
        r'^.{6}'
        label_field = t.value[0:5].strip()
        continuation_char = t.value[5]

        if continuation_char not in (' ', '0', '\n'):
            self.pending_newline = False    # ignore the newline from the previous line
            t.lexer.begin('stmt')
            return None

        # if its not a continuation line we need to send the \n from the previous line
        if self.pending_newline:
           self.pending_newline = False
           t.lexer.lexpos -= 6       # rewind so that we can read the labels, if any
           t.type = 'NEWLINE'
           t.value = '\n'
           return t

        if label_field:
            t.type = 'LABEL'
            t.value = int(label_field)
            t.lexer.begin('stmt')
            return t
        
        t.lexer.begin('stmt')
        return None

    def t_INITIAL_error(self, t):
        self.errors.append(
            LexError(f"Illegal char in columns 1-6: '{t.value[0]}' at line {t.lineno}")
        )
        t.lexer.skip(1)

    # ---------- STATEMENT (cols 7+) ----------

    def t_stmt_NEWLINE(self, t):
        r'\n'
        t.lexer.lineno += 1
        self.pending_newline = True
        t.lexer.begin('INITIAL') # dont return yet, we need to check if its a continuation first
        #return t

    def t_stmt_COMMENT(self, t):
        r'![^\n]*'
        pass

    def t_stmt_DOUBLEPRECISION(self, t):
        r'DOUBLE\s+PRECISION'
        return t

    def t_stmt_POWER(self, t):
        r'\*\*'
        return t

    def t_stmt_CONCAT(self, t):
        r'//'
        return t

    def t_stmt_EQ(self, t):
        r'\.EQ\.'
        return t

    def t_stmt_NE(self, t):
        r'\.NE\.'
        return t

    def t_stmt_LE(self, t):
        r'\.LE\.'
        return t

    def t_stmt_LT(self, t):
        r'\.LT\.'
        return t

    def t_stmt_GE(self, t):
        r'\.GE\.'
        return t

    def t_stmt_GT(self, t):
        r'\.GT\.'
        return t

    def t_stmt_AND(self, t):
        r'\.AND\.'
        return t

    def t_stmt_OR(self, t):
        r'\.OR\.'
        return t

    def t_stmt_NOT(self, t):
        r'\.NOT\.'
        return t

    def t_stmt_EQV(self, t):
        r'\.EQV\.'
        return t

    def t_stmt_NEQV(self, t):
        r'\.NEQV\.'
        return t

    def t_stmt_TRUE(self, t):
        r'\.TRUE\.'
        t.value = True
        return t

    def t_stmt_FALSE(self, t):
        r'\.FALSE\.'
        t.value = False
        return t

    def t_stmt_DOUBLE_LITERAL(self, t):
        r'(\d+\.\d*|\.\d+|\d+)[Dd][+-]?\d+'
        t.value = float(t.value.replace('D', 'E').replace('d', 'e'))
        return t

    def t_stmt_REAL_LITERAL(self, t):
        r'(\d+\.\d*|\.\d+)([Ee][+-]?\d+)?|\d+[Ee][+-]?\d+'
        t.value = float(t.value)
        return t

    def t_stmt_INT_LITERAL(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_stmt_STRING_LITERAL(self, t):
        r"'([^']|'')*'"
        t.value = t.value[1:-1].replace("''", "'")
        return t

    def t_stmt_ID(self, t):
        r'[A-Za-z][A-Za-z0-9]*'
        upper = t.value.upper()
        t.type = keywords.get(upper, 'ID')
        t.value = upper
        return t


    def t_stmt_literal(self, t):
        r'[(),:\+\-\*/=]'
        t.type = t.value
        return t

    def t_stmt_CONTINUE(self, t):
        r'CONTINUE'
        return t

    t_stmt_ignore = ' \t'

    def t_ANY_eof(self, t): # if it reaches end of file with a pending newline, send it
        if self.pending_newline:
            self.pending_newline = False
            t.type = 'NEWLINE'
            t.value = '\n'
            return t
        return None
        
    def t_stmt_error(self, t):
        r'.'
        self.errors.append(
            LexError(f"Illegal character '{t.value[0]}' at line {t.lineno}")
        )
        t.lexer.skip(1)


def build_lexer():
    return FortranLexer()