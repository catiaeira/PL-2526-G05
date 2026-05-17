class TestProgram:
    def __init__(self, filename, should_pass, description=""):
        self.filename = filename
        self.should_pass = should_pass
        self.description = description

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
    TestProgram("invalid_syntax.f", should_pass=False),
    TestProgram("invalid_semantics.f", should_pass=False),
    TestProgram("invalid_scoping.f", should_pass=False),
    TestProgram("invalid_array_index.f", should_pass=False),
    TestProgram("invalid_routine_arguments.f", should_pass=False),
    TestProgram("invalid_dup_lab_var.f", should_pass=False),
    TestProgram("invalid_subr_as_func.f", should_pass=False),
    TestProgram("invalid_unary.f", should_pass=False),
    TestProgram("invalid_stress_test_1.f", should_pass=False),
    TestProgram("invalid_stress_test_2.f", should_pass=False),
]

def get_valid_programs():
    return [p for p in ALL_TESTS if p.should_pass]

def get_invalid_programs():
    return [p for p in ALL_TESTS if not p.should_pass]