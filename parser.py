import ply.yacc as yacc
from lexer import build_lexer, tokens

class ParseError(Exception):
    pass

# ─────────────────────────────────────────────
# TOP LEVEL
# ─────────────────────────────────────────────

def p_file(p):
    r"""
    File : File TopLevel
         | TopLevel
         | File NEWLINE
         | NEWLINE
    """
    if len(p) == 3:
        if p[2] == "\n":
            p[0] = p[1]
        else:
            p[1].append(p[2])
            p[0] = p[1]
    else:
        if p[1] == "\n":
            p[0] = []
        else:
            p[0] = [p[1]]

def p_top_level(p):
    r"""
    TopLevel : MainProgram
             | SubroutineDef
             | FunctionDef
    """
    p[0] = p[1]

# PROGRAM hello
# ...
# (end of file)
def p_main_program(p):
    r"""
    MainProgram : PROGRAM ID NEWLINE Block END
    """
    p[0] = {
        "node": "program",
        "name": p[2],
        "body": p[4]
    }

# a sequence of one or more statements
#   x = 1
#   y = 2
#   z = 3
def p_block(p):
    r"""
    Block : Block Line
          | Line
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

# labeled statement:
#   10 CONTINUE
# unlabeled statement:
#   PRINT *, X
def p_line(p):
    r"""
    Line : LABEL Stmt
         | Stmt
    """
    if len(p) == 3:
        p[0] = {
            "node": "labeled_statement",
            "label": p[1],
            "statement": p[2]
        }
    else:
        p[0] = p[1]


# any single executable or declarative line
#   PRINT *, X        <- PrintStmt
#   INTEGER I         <- TypeDecl
#   IF (X .GT. 0) ... <- IfStmt
def p_stmt(p):
    r"""
    Stmt : AssignStmt
         | TypeDecl
         | PrintStmt
         | WriteStmt
         | ReadStmt
         | IfStmt
         | DoStmt
         | GotoStmt
         | CallStmt
         | ReturnStmt
         | StopStmt
         | ContinueStmt
         | ParamStmt
         | SaveStmt
    """
    p[0] = p[1]


# ─────────────────────────────────────────────
# DATA TYPES
# ─────────────────────────────────────────────

# INTEGER I
# REAL X
# DOUBLE PRECISION D
# (empty means no type prefix, treated as void)
def p_type(p):
    r"""
    Type : INTEGER
         | REAL
         | CHARACTER
         | DOUBLEPRECISION
         | LOGICAL
         | COMPLEX
    """
    p[0] = "void" if p[1] is None else p[1]

# ─────────────────────────────────────────────
# DECLARATIONS
# ─────────────────────────────────────────────

# INTEGER I, J, K
# REAL X(10), Y
def p_type_decl(p):
    r"""
    TypeDecl : Type VarList NEWLINE
    """
    p[0] = {
        "node": "variable_declaration",
        "data_type": p[1],
        "variables": p[2]
    }


# I, J, K
# X(10), Y, Z(5)
def p_var_list(p):
    r"""
    VarList : VarList "," VarDecl
            | VarDecl
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# plain scalar:  I
# array:         A(10)
# assumed-size:  A(*)  not handled
def p_var_decl(p):
    r"""
    VarDecl : ID
            | ID "(" Dims ")"
    """
    if len(p) == 2:
        p[0] = {
            "node": "variable",
            "name": p[1]
        }
    else:
        p[0] = {
            "node": "variable",
            "name": p[1],
            "dimensions": p[3]
        }


# A(10, 20)   <- two dimension bounds
# B(5)        <- one dimension bound
def p_dims(p):
    r"""
    Dims : INT_LITERAL "," INT_LITERAL
         | INT_LITERAL
    """
    if len(p) == 2:
        p[0] = {
            "node": "dimension",
            "first_dim": p[1],
            "second_dim": None
        }
    else:
        p[0] = {
            "node": "dimension",
            "first_dim": p[1],
            "second_dim": p[3]
        }


# PARAMETER (PI = 3.14159, N = 100)
def p_param_stmt(p):
    r"""
    ParamStmt : PARAMETER "(" ParamItems ")" NEWLINE
    """
    p[0] = {
        "node": "parameter_statement",
        "parameters": p[3]
    }


# PI = 3.14159, N = 100
def p_param_items(p):
    r"""
    ParamItems : ParamItems "," ParamItem
               | ParamItem
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# PI = 3.14159
def p_param_item(p):
    r"""
    ParamItem : ID "=" Expr
    """
    p[0] = {
        "node": "named_constant",
        "name": p[1],
        "value": p[3]
    }

# SAVE X, Y    <- keep specific variables between calls
# SAVE         <- keep all local variables
def p_save_stmt(p):
    r"""
    SaveStmt : SAVE VarList NEWLINE
             | SAVE NEWLINE
    """
    p[0] = {
        "node": "save_statement",
        "variables": p[2] if len(p) == 4 else []
    }

# ─────────────────────────────────────────────
# FUNCTION & SUBROUTINE
# ─────────────────────────────────────────────

# REAL FUNCTION ADD(A, B)
#   ADD = A + B
# END
def p_func_def(p):
    r"""
    FunctionDef : Type FUNCTION ID "(" Params ")" NEWLINE Block END
    """
    p[0] = {
        "node": "function",
        "name": p[3],
        "return_type": p[1],
        "parameters": p[5],
        "body": p[8]
    }


# SUBROUTINE SWAP(A, B)
#   ...
# END
def p_sub_def(p):
    r"""
    SubroutineDef : SUBROUTINE ID "(" Params ")" NEWLINE Block END
    """
    p[0] = {
        "node": "subroutine",
        "name": p[2],
        "parameters": p[4],
        "body": p[7]
    }

# ADD(A, B)  ->  Params = [A, B]
# NONE       ->  Params = []
def p_params(p):
    r"""
    Params : Params "," Param
           | Param
           | empty
    """
    if len(p) == 2:
        p[0] = [] if p[1] is None else [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# a single parameter name: A
def p_param(p):
    r"""
    Param : ID
    """
    p[0] = {
        "node": "parameter",
        "name": p[1]
    }

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
def p_if_stmt(p):
    r"""
    IfStmt : IF "(" Expr ")" THEN NEWLINE Block IfClose
           | IF "(" Expr ")" Stmt
    """
    if p[5] == "THEN":
        p[0] = {
            "node": "if_statement",
            "condition": p[3],
            "then_branch": p[7],
            "elseif_branches": p[8].get("elseif_branches", []),
            "else_branch": p[8].get("else_branch", None)
        }
    else:
        p[0] = {
            "node": "if_statement",
            "condition": p[3],
            "then_branch": [p[5]],
            "elseif_branches": [],
            "else_branch": None
        }

# collects optional ELSEIF chains, optional ELSE, then ENDIF
def p_if_close(p):
    r"""
    IfClose : ElseIfs Else ENDIF NEWLINE
            | ElseIfs ENDIF NEWLINE
    """
    if len(p) == 5:
        p[0] = {
            "elseif_branches": p[1],
            "else_branch": p[2]
        }
    else:
        p[0] = {
            "elseif_branches": p[1],
            "else_branch": None
        }

# zero or more ELSEIF branches
def p_else_ifs(p):
    r"""
    ElseIfs : ElseIfs ElseIf
            | empty
    """
    if len(p) == 2:
        p[0] = []
    else:
        p[0] = p[1] + [p[2]]

# ELSEIF (X .EQ. 0) THEN
#   PRINT *, 'ZERO'
def p_else_if(p):
    r"""
    ElseIf : ELSEIF "(" Expr ")" THEN NEWLINE Block
    """
    p[0] = {
        "node": "elseif_branch",
        "condition": p[3],
        "body": p[7]
    }

# ELSE
#   PRINT *, 'NEG'
def p_else(p):
    r"""
    Else : ELSE NEWLINE Block
    """
    p[0] = p[3]

# ─────────────────────────────────────────────
# CONTROL FLOW — DO
# ─────────────────────────────────────────────

# without step:  DO 10 I = 1, N
# with step:     DO 10 I = 1, N, 2
#   ...body...
# 10 CONTINUE
def p_do_stmt(p):
    r"""
    DoStmt : DO INT_LITERAL ID "=" Expr "," Expr NEWLINE
           | DO INT_LITERAL ID "=" Expr "," Expr "," Expr NEWLINE
    """
    if len(p) == 9:
        p[0] = {
            "node": "do_loop",
            "label": p[2],
            "loop_variable": p[3],
            "start": p[5],
            "end": p[7],
            "step": None
        }
    else:
        p[0] = {
            "node": "do_loop",
            "label": p[2],
            "loop_variable": p[3],
            "start": p[5],
            "end": p[7],
            "step": p[9]
        }


# 10 CONTINUE  <- loop target label (also valid as a standalone no-op)
def p_continue_stmt(p):
    r"""
    ContinueStmt : CONTINUE NEWLINE
    """
    p[0] = {
        "node": "continue_statement"
    }

# ─────────────────────────────────────────────
# CONTROL FLOW — GOTO
# ─────────────────────────────────────────────

# unconditional:  GOTO 100
# computed:       GOTO (10, 20, 30), I  <- jumps to label 10, 20, or 30 based on I
def p_goto_stmt(p):
    r"""
    GotoStmt : GOTO INT_LITERAL NEWLINE
             | GOTO "(" LabelList ")" "," Expr NEWLINE
    """
    if len(p) == 4:
        p[0] = {
            "node": "goto_statement",
            "label": p[2]
        }
    else:
        p[0] = {
            "node": "computed_goto_statement",
            "labels": p[3],
            "index": p[6]
        }


# (10, 20, 30)  <- list of jump targets for a computed GOTO
def p_label_list(p):
    r"""
    LabelList : LabelList "," INT_LITERAL
              | INT_LITERAL
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# ─────────────────────────────────────────────
# CALL / RETURN / STOP / PAUSE
# ─────────────────────────────────────────────

# with args:    CALL SWAP(A, B)
# without args: CALL INIT
def p_call_stmt(p):
    r"""
    CallStmt : CALL ID "(" OptExprList ")" NEWLINE
             | CALL ID NEWLINE
    """
    if len(p) == 7:
        p[0] = {
            "node": "call_statement",
            "name": p[2],
            "arguments": p[4]
        }
    else:
        p[0] = {
            "node": "call_statement",
            "name": p[2],
            "arguments": []
        }

# plain return:        RETURN
# alternate return:    RETURN 1  (jumps to 1st * label in caller's arg list)
def p_return_stmt(p):
    r"""
    ReturnStmt : RETURN NEWLINE
               | RETURN Expr NEWLINE
    """
    p[0] = {
        "node": "return_statement",
        "value": p[2] if len(p) == 4 else None
    }

# no code:      STOP
# numeric code: STOP 42
# message:      STOP 'DONE'
def p_stop_stmt(p):
    r"""
    StopStmt : STOP NEWLINE
             | STOP INT_LITERAL NEWLINE
             | STOP STRING_LITERAL NEWLINE
    """
    p[0] = {
        "node": "stop_statement",
        "code": p[2] if len(p) == 4 else None
    }

# ─────────────────────────────────────────────
# I/O — PRINT / WRITE / READ
# ─────────────────────────────────────────────

# list-directed:  PRINT *, X, Y
# formatted:      PRINT 100, X, Y
def p_print_stmt(p):
    r"""
    PrintStmt : PRINT "*" "," ExprList NEWLINE
              | PRINT INT_LITERAL "," ExprList NEWLINE
    """
    p[0] = {
        "node": "print_statement",
        "format": p[2],
        "items": p[4]
    }

# to stdout list-directed:  WRITE (*, *) X, Y
# to unit with format:      WRITE (6, 100) X, Y
def p_write_stmt(p):
    r"""
    WriteStmt : WRITE "(" IOControls ")" ExprList NEWLINE
              | WRITE "(" IOControls ")" NEWLINE
    """
    p[0] = {
        "node": "write_statement",
        "controls": p[3],
        "items": p[5] if len(p) == 7 else []
    }

# short form:   READ *, X, Y
# full form:    READ (5, 100) X, Y
# no items:     READ (5, END=99)
def p_read_stmt(p):
    r"""
    ReadStmt : READ "*" "," ExprList NEWLINE
             | READ "(" IOControls ")" ExprList NEWLINE
             | READ "(" IOControls ")" NEWLINE
    """
    if p[2] == "*":
        p[0] = {
            "node": "read_statement",
            "controls": None,
            "items": p[4]
        }
    else:
        p[0] = {
            "node": "read_statement",
            "controls": p[3],
            "items": p[5] if len(p) == 7 else []
        }

# (*, *)       <- unit=*, format=*
# (6, 100)     <- unit=6, format label=100
# (UNIT=6, FMT=100, ERR=99)
def p_io_controls(p):
    r"""
    IOControls : IOControls "," IOControl
               | IOControl
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# *            <- wildcard (list-directed)
# 6            <- unit or format label
# UNIT=6       <- keyword form
def p_io_control(p):
    r"""
    IOControl : "*"
              | INT_LITERAL
              | ID "=" Expr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "io_control",
            "keyword": p[1],
            "value": p[3]
        }

# ─────────────────────────────────────────────
# ASSIGNMENT
# ─────────────────────────────────────────────

# normal:   X = 3.14
def p_assign_stmt(p):
    r"""
    AssignStmt : Target "=" Expr NEWLINE
    """
    p[0] = {
        "node": "assignment",
        "target": p[1],
        "value": p[3]
    }

def p_target(p):
    r"""
    Target : ID
           | ID "(" ExprList ")"
    """
    if len(p) == 2:
        p[0] = {
            "node": "variable_reference",
            "name": p[1]
        }
    else:
        p[0] = {
            "node": "array_reference",
            "name": p[1],
            "indices": p[3]
        }

# ─────────────────────────────────────────────
# EXPRESSIONS
# ─────────────────────────────────────────────

# PRINT *, A, B+1, 'hello'
def p_expr_list(p):
    r"""
    ExprList : ExprList "," Expr
             | Expr
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# allows empty parentheses like CALL SUB())
def p_opt_expr_list(p):
    r"""
    OptExprList : ExprList
                | empty
    """
    p[0] = p[1] if p[1] is not None else []

# entry point: every expression goes through the precedence tower
def p_expr(p):
    r"""
    Expr : EqvExpr
    """
    p[0] = p[1]

# lowest precedence: .EQV. and .NEQV.
#   A .EQV. B    <- true if A and B have the same logical value
#   A .NEQV. B   <- true if they differ
def p_eqv_expr(p):
    r"""
    EqvExpr : EqvExpr EQV OrExpr
            | EqvExpr NEQV OrExpr
            | OrExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "binary_operation",
            "operator": p[2],
            "left": p[1],
            "right": p[3]
        }

# .OR.  <- true if either operand is true
def p_or_expr(p):
    r"""
    OrExpr : OrExpr OR AndExpr
           | AndExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "binary_operation",
            "operator": ".OR.",
            "left": p[1],
            "right": p[3]
        }

# .AND.  <- true if both operands are true
def p_and_expr(p):
    r"""
    AndExpr : AndExpr AND NotExpr
            | NotExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "binary_operation",
            "operator": ".AND.",
            "left": p[1],
            "right": p[3]
        }

# .NOT.  <- logical negation
def p_not_expr(p):
    r"""
    NotExpr : NOT NotExpr
            | RelExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "unary_operation",
            "operator": ".NOT.",
            "operand": p[2]
        }

# comparison operators: .EQ. .NE. .LT. .LE. .GT. .GE.
def p_rel_expr(p):
    r"""
    RelExpr : AdditiveExpr EQ AdditiveExpr
            | AdditiveExpr NE AdditiveExpr
            | AdditiveExpr LT AdditiveExpr
            | AdditiveExpr LE AdditiveExpr
            | AdditiveExpr GT AdditiveExpr
            | AdditiveExpr GE AdditiveExpr
            | AdditiveExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "binary_operation",
            "operator": p[2],
            "left": p[1],
            "right": p[3]
        }

# addition, subtraction, and string concatenation (//)
def p_additive_expr(p):
    r"""
    AdditiveExpr : AdditiveExpr "+" MultiplicativeExpr
                 | AdditiveExpr "-" MultiplicativeExpr
                 | AdditiveExpr CONCAT MultiplicativeExpr
                 | MultiplicativeExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "binary_operation",
            "operator": p[2],
            "left": p[1],
            "right": p[3]
        }

# multiplication and division
def p_multiplicative_expr(p):
    r"""
    MultiplicativeExpr : MultiplicativeExpr "*" UnaryExpr
                       | MultiplicativeExpr "/" UnaryExpr
                       | UnaryExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "binary_operation",
            "operator": p[2],
            "left": p[1],
            "right": p[3]
        }

# unary plus and minus
def p_unary_expr(p):
    r"""
    UnaryExpr : "-" PowExpr
              | "+" PowExpr
              | PowExpr
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "unary_operation",
            "operator": p[1],
            "operand": p[2]
        }

# exponentiation — right-associative: 2**3**4 = 2**(3**4)
def p_pow_expr(p):
    r"""
    PowExpr : Atom POWER Atom
            | Atom
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {
            "node": "binary_operation",
            "operator": "**",
            "left": p[1],
            "right": p[3]
        }

# atomic values: literals, variables, function calls, parenthesised expressions
#   42        <- INT_LITERAL
#   3.14      <- REAL_LITERAL
#   1.0D-10   <- DOUBLE_LITERAL
#   'hello'   <- STRING_LITERAL
#   .TRUE.    <- TRUE
#   X         <- variable     -> VarOrCall
#   SIN(X)    <- function call -> VarOrCall
#   (A + B)   <- parenthesised expression
def p_atom(p):
    r"""
    Atom : INT_LITERAL
         | REAL_LITERAL
         | DOUBLE_LITERAL
         | STRING_LITERAL
         | TRUE
         | FALSE
         | VarOrCall
         | "(" Expr ")"
    """
    if len(p) == 4:
        p[0] = p[2]
    else:
        value = p[1]

        if isinstance(value, bool):
            p[0] = {
                "node": "logical_literal",
                "value": value
            }
        elif isinstance(value, int):
            p[0] = {
                "node": "integer_literal",
                "value": value
            }
        elif isinstance(value, float):
            p[0] = {
                "node": "real_literal",
                "value": value
            }
        elif isinstance(value, str):
            p[0] = {
                "node": "string_literal",
                "value": value
            }
        else:
            p[0] = value

# represents both a variable reference:
#   scalar:        X
#   array element: A(I)
#   multi-dim:     B(I, J)
# and a function call:
#   SIN(X)
#   MAX(A, B, C)
def p_var_or_call(p):
    r"""
    VarOrCall : ID
              | ID "(" OptExprList ")"
    """
    if len(p) == 2:
        p[0] = {
            "node": "variable_reference",
            "name": p[1]
        }
    else:
        p[0] = {
            "node": "function_call",
            "name": p[1],
            "arguments": p[3]
        }

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

# matches nothing — used for optional parts of rules
def p_empty(p):
    'empty :'
    pass

def p_error(t):
    raise ParseError(f"Unexpected token: {t.type if t else '$'} in line no. {t.lineno}")

# ─────────────────────────────────────────────
# BUILD
# ─────────────────────────────────────────────

parser = yacc.yacc(write_tables=False, debug=True)

def parse(text):
    try:
        fortran_lexer = build_lexer()
        result = parser.parse(text, lexer=fortran_lexer)
        return result
    except ParseError as e:
        print("Parsing failed:", e)
