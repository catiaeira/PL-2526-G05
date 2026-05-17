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

        # global dictionaire in which we'll keep "pre-defined functions"
        # like MOD used in example code 3
        self.__library = {
            'MOD':   {'args': 2, 'arg_types': ['INTEGER', 'INTEGER'], 'return_type': 'INTEGER'},
            'ABS':   {'args': 1, 'arg_types': ['REAL'],    'return_type': 'REAL'},
            'SIN':   {'args': 1, 'arg_types': ['REAL'], 'return_type': 'REAL'},
            'COS':   {'args': 1, 'arg_types': ['REAL'], 'return_type': 'REAL'},
            'TAN':   {'args': 1, 'arg_types': ['REAL'], 'return_type': 'REAL'},
            'SQRT':  {'args': 1, 'arg_types': ['REAL'], 'return_type': 'REAL'},
            'LOG':   {'args': 1, 'arg_types': ['REAL'], 'return_type': 'REAL'},
        }

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
    
    # ---- HELPERS ----
    
    def _get_implicit_type(self, name):
        return "INTEGER" if name[0].upper() in "IJKLMN" else "REAL"

    # type upgrader -> INTEGER can be used as REAL
    def _types_compatible(self, given, expected):
        if given == expected:
            return True
        if given == "INTEGER" and expected in ("INTEGER", "REAL"):
            return True
        return False

    # ---- VARIABLES ----

    # declare a new variable (could be scalar or an array)
    def declare_var(self, id, vtype=None, fst_d=None, snd_d=None):
        id = id.upper()
        scope = self.current_var_scope()

        if id in scope:
            # if it exists but the type is "UNKNOWN", update it instead of raising an error.
            if scope[id]["type"] == "UNKNOWN":
                scope[id]["type"] = vtype or self._get_implicit_type(id)
                scope[id]["is_array"] = fst_d is not None
                scope[id]["fst_dim"] = fst_d
                scope[id]["snd_dim"] = snd_d
                return
            raise SemanticError(f"Duplicate declaration of variable: {id}")
    
        scope[id] = {
            "initialized": False,
            "type": vtype or self._get_implicit_type(id),
            "is_array": fst_d is not None,
            "fst_dim": fst_d,
            "snd_dim": snd_d
        }
    
    # return the variable info, but only if declared
    def lookup_var(self, id):
        id = id.upper()
        scope = self.current_var_scope()

        if id in scope:
            return scope.get(id)
        return None # return None instead of raising Undeclared Variable to allow the caller to decide if it should be declared implicitly or not

    # mark a variable as initialized, implicitly declare it if not existent
    def initialize(self, id):
        id = id.upper()
        var = self.lookup_var(id)
        if not var:
            self.declare_var(id)  # implicit typing
            var = self.lookup_var(id)
        var["initialized"] = True

    # ---- FUNCTIONS / SUBROUTINES ----

    # declare a program, function or subroutine
    def declare_routine(self, id, fkind, params=None, ret_type=None):
        if id in self.__functions:
            raise SemanticError(f"Duplicate declaration of routine: {id}")

        self.__functions[id] = {
            "kind": fkind, # to differentiate between func, subroutine, program
            "parameters": params or [],
            "return_type": (ret_type or "VOID").upper()
        }

    def update_routine_signature(self, id, actual_params):
        if id in self.__functions:
            self.__functions[id]["parameters"] = actual_params
        else:
            raise SemanticError(f"Cannot update signature of undeclared routine: {id}")
    
    # return function info, but only if declared
    def lookup_routine(self, id):
        if id not in self.__functions:
            raise SemanticError(f"Undeclared routine: {id}")
        return self.__functions[id]
    
    # Semantic constraints on functions:
    # (1) must be declared before use
    # (2) must call the correct number of arguments
    # (3) types of the arguments used must match function parameter types
    # (4) return type must be compatible

    def check_routine_call(self, id, argument_types):
        func = self.lookup_routine(id) # Raises SemanticError if not declared
        
        # Check number of arguments
        if len(argument_types) != len(func['parameters']):
            raise SemanticError(f"Routine {id} expects {len(func['parameters'])} args, got {len(argument_types)}") # (2)
        
        # Check argument types
        for i, (given, param) in enumerate(zip(argument_types, func['parameters'])):
            expected = param['type']
            if not self._types_compatible(given, expected):
                raise SemanticError(f"Routine {id} arg {i+1} ({param['name']}): expected {expected}, got {given}")
        
        return func['kind'], func['return_type']
        # constraint (4) should be checked by the caller

    # ---- LIBRARY ----

    def lookup_library(self, id):
        if id not in self.__library:
            raise SemanticError(f"Function not in library: {id}")
        return self.__library.get(id)
    
    # follow the same constraints as functions
    def check_lib_call(self, id, argument_types):
        func = self.lookup_library(id) # (1)
        
        if len(argument_types) != func['args']:
            raise SemanticError(f"Library function {id} expects {func['args']} args, got {len(argument_types)}") # (2)
        
        for i, (given, expected) in enumerate(zip(argument_types, func['arg_types'])):
            if not self._types_compatible(given, expected):
                raise SemanticError(f"Library function {id} arg {i+1}: expected {expected}, got {given}")
        
        return "function", func['return_type']
        # constraint (4) should be checked by the caller

    # unified caller
    def check_call(self, id, argument_types):
            if id in self.__library:
                return self.check_lib_call(id, argument_types)
            if id in self.__functions:
                return self.check_routine_call(id, argument_types)

            raise SemanticError(f"Undeclared routine or library function: {id}")

    # ---- LABELS ----
    
    # For labels, we'll distinguish between a declared label and a defined label.
    # This will allow "forward jumps", for example:

    #    DO 30 I = 1, 5             # declared label 30
    #       READ *, NUMS(I)
    #       SOMA = SOMA + NUMS(I)
    # 30 CONTINUE                   # defined label 30

    # Labels may de declared multiple times, as long as they're defined once and only once.

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
            else:
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
        for scope in self.__label_scopes:
            for label, info in scope.items():
                if info.get("declared") and not info.get("defined"):
                    raise SemanticError(f"Label referenced but never defined: {label}")
            
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

        print("\nLibrary Functions:")
        for name, info in self.__library.items():
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