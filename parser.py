import ply.yacc as yacc
from lexer import build_lexer, tokens
from symbol_table import SemanticError, SymbolTable

class ParseError(Exception):
    pass

# ─────────────────────────────────────────────
# TOP LEVEL
# ─────────────────────────────────────────────

# PROGRAM hello
# ...
# (end of file)

def p_code(p):
    r"""
    Code : Code CodeSegment
         | CodeSegment
    """
    if len(p) == 3:
        p[1].append(p[2])
        p[0] = p[1]
    else:
        p[0] = [p[1]]

def p_codeSegment(p):
    r"""
    CodeSegment : Program
                | SubroutineDeclaration
    """
    p[0] = p[1]

def p_program(p):
    r"""
    Program : PROGRAM ID NEWLINE Statements END OptNewline
    """
    #p.parser.symbols.check_undefined_labels()
    p[0] = {"type": "program", "name": p[2], "body": p[4]}
    
    # reset local symbols/labels for the next Subroutine
    #p.parser.symbols.clear_local_scope()

# a sequence of one or more statements
#   x = 1
#   y = 2
#   z = 3
def p_statements(p):
    r"""
    Statements : Statements Statement
               | Statement
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# any single executable or declarative line
#   PRINT *, X        ← Print
#   INTEGER I         ← VariableDeclaration
#   IF (X .GT. 0) ... ← IfStatement
def p_statement(p):
    r"""
    Statement : Assignment
              | VariableDeclaration
              | FunctionDeclaration
              | SubroutineDeclaration
              | Print
              | Write
              | Read
              | IfStatement
              | DoLoop
              | GotoStatement
              | CallStatement
              | ReturnStatement
              | StopStatement
              | ContinueStatement
              | DimensionStatement
              | ParameterStatement
              | CommonStatement
              | SaveStatement
              | DataStatement
              | EquivalenceStatement
              | Continuation
    """
    p[0] = p[1]

# CONTINUATION lines arrive as a token from the lexer (col 6 non-blank/non-zero)
# they are transparently joined to the previous line, so the parser
# never sees them as a standalone statement — we consume the token silently
def p_continuation(p):
    r"""
    Continuation : CONTINUATION
    """
    p[0] = None

# ─────────────────────────────────────────────
# DATA TYPES
# ─────────────────────────────────────────────

# INTEGER I
# REAL X
# DOUBLE PRECISION D
# (empty means no type prefix, treated as void)
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

# ─────────────────────────────────────────────
# DECLARATIONS
# ─────────────────────────────────────────────

# INTEGER I, J, K
# REAL X(10), Y
def p_variable_declaration(p):
    r"""
    VariableDeclaration : DataType VariableList NEWLINE
    """
    for var in p[2]:
        name = var["name"]
        #p.parser.symbols.declare_var(name, p[1])
    p[0] = {"type": "declaration", "dtype": p[1], "variables": p[2]}

# I, J, K
# X(10), Y, Z(5)
def p_variable_list(p):
    r"""
    VariableList : VariableList "," VariableDeclarator
                 | VariableDeclarator
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# plain scalar:  I
# array:         A(10)
# assumed-size:  A(*)  handled via DimSpec
def p_variable_declarator(p):
    r"""
    VariableDeclarator : ID
                       | ID "(" DimList ")"
    """
    if len(p) == 2:
        p[0] = {"name": p[1]}
    else:
        p[0] = {"name": p[1], "dims": p[3]}

# A(10, 20)   ← two DimSpecs
# B(5)        ← one DimSpec
def p_dim_list(p):
    r"""
    DimList : DimList "," DimSpec
            | DimSpec
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# upper bound only:    10
# explicit range:      1:10
def p_dim_spec(p):
    r"""
    DimSpec : Expression
            | Expression ":" Expression
    """
    if len(p) == 2:
        p[0] = {"upper": p[1]}
    else:
        p[0] = {"lower": p[1], "upper": p[3]}

# DIMENSION A(10), B(5, 5)
def p_dimension_statement(p):
    r"""
    DimensionStatement : DIMENSION VariableList NEWLINE
    """
    for var in p[2]:
        name = var["name"]
        #p.parser.symbols.declare_var(name, "dimension")
    p[0] = {"type": "dimension", "variables": p[2]}

# PARAMETER (PI = 3.14159, N = 100)
def p_parameter_statement(p):
    r"""
    ParameterStatement : PARAMETER "(" ParamList ")" NEWLINE
    """
    p[0] = {"type": "parameter", "params": p[3]}

# PI = 3.14159, N = 100
def p_param_list(p):
    r"""
    ParamList : ParamList "," ParamDef
              | ParamDef
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# PI = 3.14159
def p_param_def(p):
    r"""
    ParamDef : ID "=" Expression
    """
    #p.parser.symbols.declare_var(p[1], "parameter")
    #p.parser.symbols.initialize(p[1])
    p[0] = {"name": p[1], "value": p[3]}

# COMMON /BLOCK1/ X, Y  ← named block
# COMMON A, B           ← blank common
def p_common_statement(p):
    r"""
    CommonStatement : COMMON CommonBlockList NEWLINE
    """
    p[0] = {"type": "common", "blocks": p[2]}

# /BLOCK1/ X, Y  /BLOCK2/ Z
def p_common_block_list(p):
    r"""
    CommonBlockList : CommonBlockList CommonBlock
                    | CommonBlock
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# named:   /MYBLOCK/ A, B
# blank:   A, B
def p_common_block(p):
    r"""
    CommonBlock : "/" ID "/" VariableList
                | VariableList
    """
    if len(p) == 5:
        p[0] = {"block": p[2], "vars": p[4]}
    else:
        p[0] = {"block": None, "vars": p[1]}

# SAVE X, Y    ← keep specific variables between calls
# SAVE         ← keep all local variables
def p_save_statement(p):
    r"""
    SaveStatement : SAVE VariableList NEWLINE
                  | SAVE NEWLINE
    """
    p[0] = {"type": "save", "variables": p[2] if len(p) == 3 else []}


# DATA X /1.0/, I /42/
def p_data_statement(p):
    r"""
    DataStatement : DATA DataItemList NEWLINE
    """
    p[0] = {"type": "data", "items": p[2]}

# X /1.0/  I /42/
def p_data_item_list(p):
    r"""
    DataItemList : DataItemList DataItem
                 | DataItem
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# A(1), A(2) /0.0, 1.0/
# X /3*0.0/   ← repeat count: 3 copies of 0.0
def p_data_item(p):
    r"""
    DataItem : VariableList "/" DataValueList "/"
    """
    p[0] = {"vars": p[1], "values": p[3]}

# 0.0, 1.0, 2.0
def p_data_value_list(p):
    r"""
    DataValueList : DataValueList "," DataValue
                  | DataValue
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# plain value:    0.0
# repeat:         3*0.0  (shorthand for 0.0, 0.0, 0.0)
def p_data_value(p):
    r"""
    DataValue : Expression
              | INT_LITERAL "*" Expression
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"repeat": p[1], "value": p[3]}

# EQUIVALENCE (A, B), (X(1), Y)
def p_equivalence_statement(p):
    r"""
    EquivalenceStatement : EQUIVALENCE "(" EquivGroupList ")" NEWLINE
    """
    p[0] = {"type": "equivalence", "groups": p[3]}

# (A, B), (X(1), Y)
def p_equiv_group_list(p):
    r"""
    EquivGroupList : EquivGroupList "," EquivGroup
                   | EquivGroup
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# (A, B)  ← A and B share the same memory location
def p_equiv_group(p):
    r"""
    EquivGroup : "(" VariableList ")"
    """
    p[0] = p[2]


# ─────────────────────────────────────────────
# FUNCTION & SUBROUTINE
# ─────────────────────────────────────────────

# REAL FUNCTION ADD(A, B)
#   ADD = A + B
# END
def p_function_declaration(p):
    r"""
    FunctionDeclaration : DataType FUNCTION ID "(" Parameters ")" NEWLINE Statements END NEWLINE
    """
    name = p[3]
    params = p[5]
    #p.parser.symbols.declare_fun(name, p[1], params)
    #p.parser.symbols.push()
    for param in params:
        pname = param["name"]
        #p.parser.symbols.declare_var(pname, "param")
        #p.parser.symbols.initialize(pname)
    #p.parser.symbols.pop()
    p[0] = {"type": "function", "name": name, "return_type": p[1],
            "params": params, "body": p[8]}

# SUBROUTINE SWAP(A, B)
#   ...
# END
def p_subroutine_declaration(p):
    r"""
    SubroutineDeclaration : SUBROUTINE ID "(" Parameters ")" NEWLINE Statements END NEWLINE
    """
    name = p[2]
    params = p[4]
    #p.parser.symbols.declare_fun(name, "void", params)
    #p.parser.symbols.push()
    for param in params:
        pname = param["name"]
        #p.parser.symbols.declare_var(pname, "param")
        #p.parser.symbols.initialize(pname)
    #p.parser.symbols.pop()
    p[0] = {"type": "subroutine", "name": name, "params": params, "body": p[7]}

# ADD(A, B)  →  Parameters = [A, B]
# NONE       →  Parameters = []
def p_parameters(p):
    r"""
    Parameters : Parameters "," Parameter
               | Parameter
               | empty
    """
    if len(p) == 2:
        p[0] = [] if p[1] is None else [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# a single parameter name: A
def p_parameter(p):
    r"""
    Parameter : ID
    """
    p[0] = {"name": p[1]}

# ─────────────────────────────────────────────
# CONTROL FLOW — IF
# ─────────────────────────────────────────────

# block IF:
#   IF (X .GT. 0) THEN
#     PRINT *, X
#   ELSEIF (X .EQ. 0) THEN
#     PRINT *, 'ZERO'
#   ELSE
#     PRINT *, 'NEG'
#   ENDIF
#
# one-liner:
#   IF (X .GT. 0) PRINT *, X
def p_if_statement(p):
    r"""
    IfStatement : IF "(" Expression ")" THEN NEWLINE Statements EndIfClause
                | IF "(" Expression ")" Statement
    """
    if p[5] == "THEN":
        p[0] = {"type": "if", "condition": p[3],
                "then": p[7], "elseif": p[8].get("elseif", []),
                "else": p[8].get("else", None)}
    else:
        p[0] = {"type": "if", "condition": p[3],
                "then": [p[5]], "elseif": [], "else": None}

# collects optional ELSEIF chains, optional ELSE, then ENDIF
def p_end_if_clause(p):
    r"""
    EndIfClause : ElseIfClauses ElseClause ENDIF NEWLINE
                | ElseIfClauses ENDIF NEWLINE
    """
    if len(p) == 5:
        p[0] = {"elseif": p[1], "else": p[2]}
    else:
        p[0] = {"elseif": p[1], "else": None}

# zero or more ELSEIF branches
def p_else_if_clauses(p):
    r"""
    ElseIfClauses : ElseIfClauses ElseIfClause
                  | empty
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]

# ELSEIF (X .EQ. 0) THEN
#   PRINT *, 'ZERO'
def p_else_if_clause(p):
    r"""
    ElseIfClause : ELSEIF "(" Expression ")" THEN NEWLINE Statements
    """
    p[0] = {"condition": p[3], "body": p[7]}

# ELSE
#   PRINT *, 'NEG'
def p_else_clause(p):
    r"""
    ElseClause : ELSE NEWLINE Statements
    """
    p[0] = p[3]

# ─────────────────────────────────────────────
# CONTROL FLOW — DO
# ─────────────────────────────────────────────

# without step:  DO 10 I = 1, N
# with step:     DO 10 I = 1, N, 2
#   ...body...
# 10 CONTINUE
def p_do_loop(p):
    r"""
    DoLoop : DO INT_LITERAL ID "=" Expression "," Expression NEWLINE Statements LabeledStatement
           | DO INT_LITERAL ID "=" Expression "," Expression "," Expression NEWLINE Statements LabeledStatement
    """
    #p.parser.symbols.define_label(p[2])
    if len(p) == 11:
        p[0] = {"type": "do", "label": p[2], "var": p[3],
                "start": p[5], "stop": p[7], "step": None, "body": p[9], "end" : p[10]}
    else:
        p[0] = {"type": "do", "label": p[2], "var": p[3],
                "start": p[5], "stop": p[7], "step": p[9], "body": p[11], "end" : p[12]}

# 10 CONTINUE  ← loop target label (also valid as a standalone no-op)
def p_continue_statement(p):
    r"""
    ContinueStatement : CONTINUE NEWLINE
    """
    p[0] = {"type": "continue"}

def p_labeled_statement(p):
    r"""
    LabeledStatement : LABEL Statement NEWLINE
                     | LABEL ContinueStatement
    """
    if p[2] == "CONTINUE":
        p[0] = p[2]
    else:
        p[0] = {"type": "statement", "body": p[2]}


# ─────────────────────────────────────────────
# CONTROL FLOW — GOTO
# ─────────────────────────────────────────────

# unconditional:  GOTO 100
# computed:       GOTO (10, 20, 30), I  ← jumps to label 10, 20, or 30 based on I
def p_goto_statement(p):
    r"""
    GotoStatement : GOTO INT_LITERAL NEWLINE
                  | GOTO "(" LabelList ")" "," Expression NEWLINE
    """
    if len(p) == 3:
        p[0] = {"type": "goto", "label": p[2]}
    else:
        p[0] = {"type": "computed_goto", "labels": p[3], "index": p[6]}

# (10, 20, 30)
def p_label_list(p):
    r"""
    LabelList : LabelList "," INT_LITERAL
              | INT_LITERAL
    """
    if len(p) == 2:
        #p.parser.symbols.declare_label(p[1])
        p[0] = [p[1]]
    else:
        #p.parser.symbols.declare_label(p[3])
        p[0] = p[1] + [p[3]]

# ─────────────────────────────────────────────
# CALL / RETURN / STOP / PAUSE
# ─────────────────────────────────────────────

# with args:    CALL SWAP(A, B)
# without args: CALL INIT
def p_call_statement(p):
    r"""
    CallStatement : CALL ID "(" ArgList ")" NEWLINE
                  | CALL ID NEWLINE
    """
    name = p[2]
    #try:
        #p.parser.symbols.lookup_fun(name)
    #except SemanticError:
        #pass  # forward references and intrinsics are allowed
    if len(p) == 7:
        p[0] = {"type": "call", "name": name, "args": p[4]}
    else:
        p[0] = {"type": "call", "name": name, "args": []}

# SWAP(A, B)  →  ArgList = [A, B]
# SIN(X)      →  ArgList = [X]
def p_arg_list(p):
    r"""
    ArgList : ArgList "," Expression
            | Expression
            | empty
    """
    if len(p) == 2:
        p[0] = [] if p[1] is None else [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# plain return:        RETURN
# alternate return:    RETURN 1  (jumps to 1st * label in caller's arg list)
def p_return_statement(p):
    r"""
    ReturnStatement : RETURN NEWLINE
                    | RETURN Expression NEWLINE
    """
    p[0] = {"type": "return", "value": p[2] if len(p) == 4 else None}

# no code:      STOP
# numeric code: STOP 42
# message:      STOP 'DONE'
def p_stop_statement(p):
    r"""
    StopStatement : STOP NEWLINE
                  | STOP INT_LITERAL NEWLINE
                  | STOP STRING_LITERAL NEWLINE
    """
    p[0] = {"type": "stop", "code": p[2] if len(p) == 4 else None}

# ─────────────────────────────────────────────
# I/O — PRINT / WRITE / READ
# ─────────────────────────────────────────────

# list-directed:  PRINT *, X, Y
# formatted:      PRINT 100, X, Y
def p_print(p):
    r"""
    Print : PRINT "*" "," ExpressionList NEWLINE
          | PRINT INT_LITERAL "," ExpressionList NEWLINE
    """
    p[0] = {"type": "print", "format": p[2], "items": p[4]}

# to stdout list-directed:  WRITE (*, *) X, Y
# to unit with format:      WRITE (6, 100) X, Y
def p_write(p):
    r"""
    Write : WRITE "(" IOControlList ")" ExpressionList NEWLINE
          | WRITE "(" IOControlList ")" NEWLINE
    """
    p[0] = {"type": "write", "controls": p[3],
            "items": p[5] if len(p) == 7 else []}

# short form:   READ *, X, Y
# full form:    READ (5, 100) X, Y
# no items:     READ (5, END=99)
def p_read(p):
    r"""
    Read : READ "*" "," VariableList NEWLINE
         | READ "(" IOControlList ")" VariableList NEWLINE
         | READ "(" IOControlList ")" NEWLINE
    """
    if p[2] == "*":
        p[0] = {"type": "read", "controls": None, "items": p[4]}
    else:
        p[0] = {"type": "read", "controls": p[3],
                "items": p[5] if len(p) == 7 else []}

# (*, *)       ← unit=*, format=*
# (6, 100)     ← unit=6, format label=100
# (UNIT=6, FMT=100, ERR=99)
def p_io_control_list(p):
    r"""
    IOControlList : IOControlList "," IOControl
                  | IOControl
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# *            ← wildcard (list-directed)
# 6            ← unit or format label
# UNIT=6       ← keyword form
def p_io_control(p):
    r"""
    IOControl : "*"
              | INT_LITERAL
              | ID "=" Expression
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"key": p[1], "value": p[3]}

# ─────────────────────────────────────────────
# ASSIGNMENT
# ─────────────────────────────────────────────

# normal:   X = 3.14
# ASSIGN:   ASSIGN 100 TO ILABEL  (stores label number in variable)
def p_assignment(p):
    r"""
    Assignment : Variable "=" Expression NEWLINE
               | ASSIGN INT_LITERAL TO Variable NEWLINE
    """
    if p[2] == "=":
        #var = p[1]["name"]
        #p.parser.symbols.initialize(var)
        p[0] = {"type": "assignment", "variable": p[1], "expression": p[3]}
    else:
        #var = p[4]["name"]
        #p.parser.symbols.initialize(var)
        p[0] = {"type": "assign", "label": p[2], "variable": p[4]}

# ─────────────────────────────────────────────
# EXPRESSIONS
# ─────────────────────────────────────────────

# PRINT *, A, B+1, 'hello'
def p_expression_list(p):
    r"""
    ExpressionList : ExpressionList "," Expression
                   | Expression
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# entry point: every expression goes through the precedence tower
def p_expression(p):
    r"""
    Expression : LogicalExpression
               | ArithmeticExpression
    """
    p[0] = p[1]

# lowest precedence: .EQV. and .NEQV.
#   A .EQV. B    ← true if A and B have the same logical value
#   A .NEQV. B   ← true if they differ
def p_logical_expression_eqv(p):
    r"""
    LogicalExpression : LogicalExpression EQV LogicalOrExpr
                      | LogicalExpression NEQV LogicalOrExpr
                      | LogicalOrExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "binop", "op": p[2], "left": p[1], "right": p[3]}

# .OR.  ← true if either operand is true
#   X .GT. 0 .OR. Y .GT. 0
def p_logical_or(p):
    r"""
    LogicalOrExpr : LogicalOrExpr OR LogicalAndExpr
                  | LogicalAndExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "binop", "op": ".OR.", "left": p[1], "right": p[3]}

# .AND.  ← true if both operands are true
#   X .GT. 0 .AND. Y .GT. 0
def p_logical_and(p):
    r"""
    LogicalAndExpr : LogicalAndExpr AND LogicalNotExpr
                   | LogicalNotExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "binop", "op": ".AND.", "left": p[1], "right": p[3]}

# .NOT.  ← logical negation
#   .NOT. FLAG
def p_logical_not(p):
    r"""
    LogicalNotExpr : NOT RelationalExpr
                   | RelationalExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "unop", "op": ".NOT.", "operand": p[2]}

# comparison operators: .EQ. .NE. .LT. .LE. .GT. .GE.
#   I .GE. 1 .AND. I .LE. 10
def p_relational_expression(p):
    r"""
    RelationalExpr : ArithmeticExpression EQ ArithmeticExpression
                   | ArithmeticExpression NE ArithmeticExpression
                   | ArithmeticExpression LT ArithmeticExpression
                   | ArithmeticExpression LE ArithmeticExpression
                   | ArithmeticExpression GT ArithmeticExpression
                   | ArithmeticExpression GE ArithmeticExpression
                   | ArithmeticExpression
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "binop", "op": p[2], "left": p[1], "right": p[3]}

# addition, subtraction, string concatenation (//)
#   A + B - C
#   'HEL' // 'LO'
def p_arithmetic_add(p):
    r"""
    ArithmeticExpression : ArithmeticExpression "+" Term
                         | ArithmeticExpression "-" Term
                         | ArithmeticExpression CONCAT Term
                         | Term
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "binop", "op": p[2], "left": p[1], "right": p[3]}

# multiplication and division
#   A * B / C
def p_term(p):
    r"""
    Term : Term "*" PowerExpr
         | Term "/" PowerExpr
         | PowerExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "binop", "op": p[2], "left": p[1], "right": p[3]}

# exponentiation — right-associative: 2**3**4 = 2**(3**4)
#   X**2
#   2**N**M
def p_power_expr(p):
    r"""
    PowerExpr : UnaryExpr POWER PowerExpr
              | UnaryExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "binop", "op": "**", "left": p[1], "right": p[3]}

# unary plus and minus
#   -X
#   +1
def p_unary_expr(p):
    r"""
    UnaryExpr : "-" Primary
              | "+" Primary
              | Primary
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {"type": "unop", "op": p[1], "operand": p[2]}

# atomic values: literals, variables, function calls, parenthesised expressions
#   42        ← INT_LITERAL
#   3.14      ← REAL_LITERAL
#   1.0D-10   ← DOUBLE_LITERAL
#   'hello'   ← STRING_LITERAL
#   .TRUE.    ← TRUE
#   X         ← Variable
#   SIN(X)    ← FunctionCall
#   (A + B)   ← parenthesised expression
def p_primary(p):
    r"""
    Primary : INT_LITERAL
            | REAL_LITERAL
            | DOUBLE_LITERAL
            | STRING_LITERAL
            | TRUE
            | FALSE
            | Variable
            | FunctionCall
            | "(" Expression ")"
    """
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = p[1]

# intrinsic or user-defined function call used inside an expression
#   SIN(X)
#   MAX(A, B, C)
def p_function_call(p):
    r"""
    FunctionCall : ID "(" ArgList ")"
    """
    name = p[1]
    #try:
        #p.parser.symbols.lookup_fun(name)
    #except SemanticError:
        #pass  # intrinsic functions won't be in the symbol table
    p[0] = {"type": "call_expr", "name": name, "args": p[3]}

# ─────────────────────────────────────────────
# VARIABLES
# ─────────────────────────────────────────────

# HOLLERITH literals (nH...) can appear in FORMAT statements and DATA
# e.g.  5HHELLO  is equivalent to 'HELLO' in old Fortran
# we treat them as string primaries so they can appear in expressions
def p_primary_hollerith(p):
    r"""
    Primary : HOLLERITH
    """
    p[0] = {"type": "hollerith", "value": p[1]}

# scalar:        X
# array element: A(I)
# multi-dim:     B(I, J)
def p_variable(p):
    r"""
    Variable : ID
             | ID "(" NumOrIndexList ")"
    """
    name = p[1]
    #try:
        #p.parser.symbols.lookup_var(name)
    #except SemanticError:
        #pass  # undeclared variables caught properly at initialization time

    if len(p) == 2:
        p[0] = {"type": "variable", "name": name}
    else:
        p[0] = {"type": "array", "name": name, "indices": p[3]}

# A(I, J)  →  NumOrIndexList = [I, J]
def p_num_or_index_list(p):
    r"""
    NumOrIndexList : NumOrIndexList "," NumOrIndex
                   | NumOrIndex
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# an index is just a full expression: I, I+1, N-1, etc.
def p_num_or_index(p):
    r"""
    NumOrIndex : Expression
    """
    p[0] = p[1]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def p_opt_newline(p):
    r"""
    OptNewline : NEWLINE
               | empty
    """
    pass

# matches nothing — used for optional parts of rules
def p_empty(p):
    'empty :'
    pass

def p_error(t):
    raise ParseError(f"Unexpected token: {t.type if t else '$'}")

# ─────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────

parser = yacc.yacc(write_tables=False, debug=True)

def parse(text):
    try:
        fortran_lexer = build_lexer()
        parser.symbols = SymbolTable()
        result = parser.parse(text, lexer=fortran_lexer)
        print("Program is semantically correct")
        return result
    except ParseError as e:
        print("Parsing failed:", e)
    except SemanticError as e:
        print("Semantic error:", e)