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

        self.errors = []

    # ---- VAR SCOPES MANAGEMENT ----

    def push_var_scope(self):
        self.__variable_scopes.append({})

    def pop_var_scope(self):
        if len(self.__variable_scopes) == 1:
            self.errors.append(SemanticError("Cannot pop global variable scope"))
        self.__variable_scopes.pop()

    def current_var_scope(self):
        return self.__variable_scopes[-1]

    # ---- LABEL SCOPES MANAGEMENT ----

    def push_label_scope(self):
        self.__label_scopes.append({})

    def pop_label_scope(self):
        if len(self.__label_scopes) == 1:
            self.errors.append(SemanticError("Cannot pop global label scope"))
        self.__label_scopes.pop()

    def current_label_scope(self):
        return self.__label_scopes[-1]
    
    # ---- VARIABLES ----

    # declare a new variable
    def declare_var(self, id, vtype):
        scope = self.current_var_scope()

        if id in scope:
            self.errors.append(SemanticError(f"Duplicate declaration of variable: {id}"))
      
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
        self.errors.append(SemanticError(f"Undeclared variable: {id}"))

    # mark a variable as initialized, but only if declared
    def initialize(self, id):
        iden = self.lookup_var(id) # already raises an error if the variable is undeclared
        iden["initialized"] = True

    def is_initialized(self, id):
        return self.lookup_var(id)["initialized"]

    def get_var_type(self, id):
        return self.lookup_var(id)["type"]

    # ---- FUNCTIONS / SUBROUTINES ----

    # declare a program, function or subroutine
    def declare_routine(self, id, fkind, params=None, ret_type=None):
        if id in self.__functions:
            self.errors.append(SemanticError(f"Duplicate declaration of routine: {id}"))

        if params is None: params = []

        self.__functions[id] = {
            "kind": fkind, # not sure if we'll need to differentiate between func, subroutine, program(?)
            "parameters": params,
            "return_type": ret_type
        }

    # return function info, but only if declared
    def lookup_routine(self, id):
        if id not in self.__functions:
            self.errors.append(SemanticError(f"Undeclared routine: {id}"))
        return self.__functions.get(id)
    
    # Semantic constraints on functions:
    # (1) must be declared before use
    # (2) must call the correct number of arguments
    # (3) types of the arguments used must match function parameter types
    # (4) return type must be compatible

    def check_fun_call(self, id, args, eval_expr):
        func = self.lookup_routine(id) # already raises an error if the function is undeclared # (1)

        expected_len = len(func["parameters"])
        given_len = len(args)

        if expected_len != given_len:
            self.errors.append(SemanticError(f"Function '{id}': expected {expected_len} arguments, got {given_len}")) # (2)

        for arg_node, param in zip(args, func["parameters"]):
            arg_type = eval_expr(arg_node)
            param_type = param["type"]
    
            if arg_type != param_type:
                self.errors.append(SemanticError(f"Type mismatch in call to '{id}': expected {param_type}, got {arg_type}")) # (3)
    
        return func["kind"], func["return_type"] # constraint (4) should be checked by the caller
        # return (kind, return_type) so that the caller can differentiate between functions and subroutines and check the return type

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
                self.errors.append(SemanticError(f"Duplicate definition of label: {label}"))
            scope[label]["defined"] = True
        else:
            scope[label] = {
                "defined": True,
                "declared": False
            }

    def lookup_label(self, label):
        scope = self.current_label_scope()

        if label not in scope or not scope[label]["defined"]:
            self.errors.append(SemanticError(f"Undefined label: {label}"))

        return scope[label]

    # should be used in a posterior sweep to make sure all declared labels are defined
    def check_undefined_labels(self):
        for scope in self.__label_scopes:
            for label, info in scope.items():
                if info.get("declared") and not info.get("defined"):
                    self.errors.append(SemanticError(
                        f"Label referenced but never defined: {label}"
                    ))
            
    # ---- DEBUG ----

    def dump(self):
        print("\n=== SYMBOL TABLE ===")

        for i, scope in enumerate(self.__variable_scopes):
            print(f"\nVariable Scope {i}:")
            for name, info in scope.items():
                print(f"  {name}: {info}")

        print("\nFunctions & Subroutines:")
        for name, info in self.__functions.items():
            print(f"  {name}: {info}")

        for i, scope in enumerate(self.__label_scopes):
            print(f"\nLabel Scope {i}:")
            for label, info in scope.items():
                status = []
                if info.get("declared"):
                    status.append("declared")
                if info.get("defined"):
                    status.append("defined")

                print(f"  {label}: {', '.join(status) if status else 'empty'}")