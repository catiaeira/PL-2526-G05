import ply.yacc as yacc
from lexer import tokens

class SyntaxError(Exception):
    pass

def p_program(p):
    r"""
    Program : PROGRAM STRING_LITERAL NEWLINE Statements
    """
    p[0] = p[2] + p[4]

def p_statements(p):
    r"""
    Statements : Statements Statement
               | Statement
    Statement : Assignment
              | VariableDeclaration
              | FunctionDeclaration
              | Print
              | Read
    """
    if len(p) == 2:
      p[0] = p[1]
    else:
      p[0] = p[1] + p[2]

def p_function_declaration(p):
    r"""
    FunctionDeclaration : DataType FUNCTION ID "(" Parameters ")" NEWLINE Statements END
    """
    p[0] = {"type": "function", "return_type": p[1], "name": p[3], "params": p[5], "statements": p[8]}

def p_data_type(p):
    r"""
    DataType : INTEGER
             | REAL
             | CHARACTER
             | DOUBLEPRECISION
             | LOGICAL
             | COMPLEX
             | empty
    """
    p[0] = "void" if p[1] is None else p[1]

def p_parameters(p):
    r"""
    Parameters : Parameters "," Parameter
               | Parameter
               | empty
    Parameter  : Variable
    """
    if len(p) == 2:
        p[0] = [] if p[1] is None else [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_empty(p):
    'empty :'
    pass

def p_variable(p):
    r"""
    Variable : ID
             | ID "(" NumOrIndex ")"
    """
    if len(p) == 2:
        p[0] = {"type": "variable", "name": p[1]}
    else:
        p[0] = {"type": "array", "name": p[1], "index": p[3]}

def p_num_or_index(p): #to do: verificar
    r"""
    NumOrIndex : INT_LITERAL
               | ID
    """
    p[0] = p[1]

def p_variable_declaration(p):
    r"""
    VariableDeclaration : DataType VariableList NEWLINE
    """
    p[0] = {"type": "declaration", "data_type": p[1], "variables": p[2]}

def p_variable_list(p):
    r"""
    VariableList : VariableList "," Variable
                 | Variable
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_print(p):
    r"""
    Print : PRINT "*" "," ExpressionList NEWLINE
    """
    p[0] = {"type": "print", "expression": p[4]}

def p_expression_list(p):
    r"""
    ExpressionList : ExpressionList "," Expression
                   | Expression
    """
    if len(p) == 1:
        p[0] = {"type": "print", "expression": [p[1]]}
    else:
        p[0] = {"type": "print", "expression": p[1] + [p[3]]}

def p_expression(p):
    r"""
    Expression : ArithmeticExpression
               | LogicalExpression
               | STRING_LITERAL
               | Variable
    """
    p[0] = p[1]

def p_arithmetic_expression(p): #to do: fix (podem ser indicadas variáveis)
    r"""
    ArithmeticExpression : NumType "+" NumType
                         | NumType "-" NumType
                         | NumType "*" NumType
                         | NumType "/" NumType
                         | "(" ArithmeticExpression ")"
                         | NumType
    """
    #to do: fix + finish lol

def p_logical_expression(p):
    #to do
    r"""
    """

def p_read(p): #mencionar que só estamos a cobrir o "short read" aqui, o "long read" é mais complexo e não é necessário para o nosso projeto #sourcetrustme
    r"""
    Read : READ '*' ',' VariableList
    """
    p[0] = {"type": "read", "input": p[4]}

def p_assignment(p):
    r"""
    Assignment : Variable "=" Expression NEWLINE
               | ASSIGN Expression TO Variable NEWLINE
    """
    if p[2] == "=":
        p[0] = {"type": "assignment", "variable": p[1], "expression": p[3]}
    else:
        p[0] = {"type": "assignment", "variable": p[4], "expression": p[2]}






class ParseError(Exception):
  pass

def p_error(t):
  raise ParseError(f"Unexpected token: {t.type if t else '$'}")

parser = yacc.yacc(write_tables=False, debug=False)