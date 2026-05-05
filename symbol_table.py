class SemanticError(Exception):
    pass

class SymbolTable:
    def __init__(self):
        # stack of scopes for variables (each one is a dictionaire)
        # {"initialized" = True | False, "type" = INTEGER | etc}
        self.__variable_scopes = [{}]

        # function/subroutine dictionaire (global)
        # {"kind" = "function" | "subroutine" | "program" (?), "parameters" = [param1, param2, ...], "return_type" = None | INTEGER | etc}
        self.__functions = {}
        # things like PROGRAM, FUNCTION, SUBROUTINE, are all top level
        # declarations, which means they can't be nested. Then, we can
        # keep a separate dict regarding them.

        # labels (for GOTO / DO)
        # stack of scopes for labels (each one is a dictionaire)
        # {"defined" = True | False, "declared" = True | False}
        self.__label_scopes = [{}]
        # labels are NOT global assets, so we keep them in scopes as well

    # ---- VAR SCOPES MANAGEMENT ----

    def push_var_scope(self):
        self.__variable_scopes.append({})

    def pop_var_scope(self):
        if len(self.__variable_scopes) == 1:
            raise SemanticError("Cannot pop global variable scope")
        self.__variable_scopes.pop()

    def current_var_scope(self):
        return self.__variable_scopes[-1]

    # ---- LABEL SCOPES MANAGEMENT ----

    def push_label_scope(self):
        self.__label_scopes.append({})

    def pop_label_scope(self):
        if len(self.__label_scopes) == 1:
            raise SemanticError("Cannot pop global label scope")
        self.__label_scopes.pop()

    def current_label_scope(self):
        return self.__label_scopes[-1]
    
    # ---- VARIABLES ----

    # declare a new variable
    def declare_var(self, id, vtype):
        scope = self.current_var_scope()

        if id in scope:
            raise SemanticError(f"Duplicate declaration of variable: {id}")
      
        scope[id] = {
            "initialized": False,
            "type": vtype
        }

    # return the variable info, but only if declared
    def lookup_var(self, id):
        # search all the scopes, starting with the most recent one
        for scope in reversed(self.__variable_scopes):
            if id in scope:
                return scope.get(id)
        raise SemanticError(f"Undeclared variable: {id}")

    # mark a variable as initialized, but only if declared
    def initialize(self, id):
        iden = self.lookup_var(id) # already raises an error if the variable is undeclared
        iden["initialized"] = True

    def is_initialized(self, id):
        return self.lookup_var(id)["initialized"]

    def get_var_type(self, id):
        return self.lookup_var(id)["type"]

    # ---- FUNCTIONS / SUBROUTINES ----

    # declare a function
    def declare_fun(self, id, params=None, ret_type=None):
        if id in self.__functions:
            raise SemanticError(f"Duplicate declaration of function/subroutine: {id}")

        if params is None: params = []

        self.__functions[id] = {
            "kind": "function", # not sure if we'll need to differentiate between func, subroutine, program(?)
            "parameters": params,
            "return_type": ret_type
        }

    # return function info, but only if declared
    def lookup_fun(self, id):
        if id not in self.__functions:
            raise SemanticError(f"Undeclared function: {id}")
        return self.__functions.get(id)
    
    # Semantic constraints on functions:
    # (1) must be declared before use
    # (2) must call the correct number of arguments
    # (3) types of the arguments used must match function parameter types
    # (4) return type must be compatible

    def check_fun_call(self, id, params, eval_expr):
        func = self.lookup_fun(id) # already raises an error if the function is undeclared # (1)

        expected_len = len(func["parameters"])
        given_len = len(params)

        if expected_len != given_len:
            raise SemanticError(f"Function '{id}': expected {expected_len} arguments, got {given_len}") # (2)

        for arg_node, param in zip(func["parameters"], params):
            arg_type = eval_expr(arg_node)
            param_type = param["type"]
    
            if arg_type != param_type:
                raise SemanticError(f"Type mismatch in call to '{id}': expected {param_type}, got {arg_type}") # (3)
    
        return func["return_type"] # constraint (4) should be checked by the caller

    # ---- LABELS ----
    
    # For labels, we'll distinguish between a declared label and a defined label.
    # This will allow "forward jumps", for example:

    #    DO 30 I = 1, 5             # declared label 30
    #       READ *, NUMS(I)
    #       SOMA = SOMA + NUMS(I)
    # 30 CONTINUE                   # defined label 30

    # Labels may de declared multiple times, as long as they're defined once and only once.

    # !!NOTE!! there may be DO or GOTO constraints regarding labels not yet considered

    def declare_label(self, label):
        scope = self.current_label_scope()

        if label in scope:
            scope[label]["declared"] = True
        else:
            scope[label] = {
                "defined": False,
                "declared": True
            }

    def define_label(self, label):
        scope = self.current_label_scope()

        if label in scope:
            if scope[label]["defined"]:
                raise SemanticError(f"Duplicate definition of label: {label}")
            scope[label]["defined"] = True
        else:
            scope[label] = {
                "defined": True,
                "declared": False
            }

    def lookup_label(self, label):
        scope = self.current_label_scope()

        if label not in scope or not scope[label]["defined"]:
            raise SemanticError(f"Undefined label: {label}")

        return scope[label]

    # should be used in a posterior sweep to make sure all declared labels are defined
    def check_undefined_labels(self):
        scope = self.current_label_scope()

        for label, entry in scope.items():
            if entry["declared"] and not entry["defined"]:
                raise SemanticError(
                    f"Label referenced but never defined: {label}"
                )
            
    # ---- DEBUG ----

    def dump(self):
        print("=== SYMBOL TABLE ===")
        for i, scope in enumerate(self.scopes):
            print(f"Scope {i}: {scope}")
        print("Functions:", self.functions)
        print("Labels:", self.labels)