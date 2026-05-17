class TestProgram:
    def __init__(self, filename, should_pass, syntax_errors=[], semantic_errors=[]):
        self.filename = filename
        self.should_pass = should_pass
        self.syntax_errors = syntax_errors
        self.semantic_errors = semantic_errors

ALL_TESTS = [
    # ---- Valid Programs ----
    TestProgram("exemplo1.f", should_pass=True),
    TestProgram("exemplo2.f", should_pass=True),
    TestProgram("exemplo3.f", should_pass=True),
    TestProgram("exemplo4.f", should_pass=True),
    TestProgram("exemplo5.f", should_pass=True),
    TestProgram("code.f", should_pass=True),
    TestProgram("valid_features.f", should_pass=True),
    TestProgram("valid_logic.f", should_pass=True),
    TestProgram("valid_computed_goto.f", should_pass=True),
    TestProgram("valid_2d_array.f", should_pass=True),
    TestProgram("valid_logic_ops.f", should_pass=True),

    # ---- Invalid Programs ----
    TestProgram("invalid_syntax.f", False, syntax_errors=[
        "Unexpected token: ENDIF on line 7",
        "Unexpected token: NEWLINE on line 6",
        "Unexpected token: NEWLINE on line 10",
        "Unexpected token: * on line 10"
    ]),
    TestProgram(
        filename="invalid_semantics.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "Mixing incompatible types in binary operation",
            "Label referenced but never defined: 999",
            "'MYFUNC' is a function; use in expression"
        ]
    ),
    TestProgram(
        filename="invalid_scoping.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "Undeclared variable: GLOBALVAR"
        ]
    ),
    TestProgram(
        filename="invalid_array_index.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "Array index for 'ARR' must be INTEGER"
        ]
    ),
    TestProgram(
        filename="invalid_routine_arguments.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "Routine PROCESS arg 1 (X): expected INTEGER, got REAL",
            "Routine PROCESS expects 1 args, got 2"
        ]
    ),
    TestProgram(
        filename="invalid_dup_lab_var.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "Duplicate declaration of variable: X",
            "Duplicate definition of label: 10"
        ]
    ),
    TestProgram(
        filename="invalid_subr_as_func.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "Cannot call subroutine 'LOGIT' as function",
            "Mixing incompatible types in binary operation"
        ]
    ),
    TestProgram(
        filename="invalid_unary.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            ".NOT. requires LOGICAL",
            "- requires numeric"
        ]
    ),
    TestProgram(
        filename="invalid_stress_test_1.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "IF condition must be LOGICAL",
            "Library function MOD expects 2 args, got 1",
            "Label referenced but never defined: 777",
            "'CALCVAL' is a function; use in expression"
        ]
    ),
    TestProgram(
        filename="invalid_stress_test_2.f", 
        should_pass=False, 
        syntax_errors=[],
        semantic_errors=[
            "- requires numeric",
            "Array index for 'ARR' must be INTEGER",       # !!!
            "Routine RENDER arg 1 (NUM): expected INTEGER, got REAL",
            "Duplicate declaration of variable: NUM"
        ]
    )
]


def get_valid_programs():
    return [p for p in ALL_TESTS if p.should_pass]

def get_invalid_programs():
    return [p for p in ALL_TESTS if not p.should_pass]