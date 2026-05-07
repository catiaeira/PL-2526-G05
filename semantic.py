from symbol_table import SymbolTable, SemanticError

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.errors = []

    # ---- ENTRY POINT ----

    def analyze(self, ast):
        nodes = ast if isinstance(ast, list) else [ast]

        print("\n!! BEFORE ANALYSIS !!") #debug
        self.symbols.dump() #debug

        # PASS 1: register routines
        for node in nodes:
                    node_type = node.get("type") or node.get("node")
                    if node_type in ("function", "subroutine", "program"):
                        name = node.get("name")
                        params = node.get("params", [])
                        self.symbols.declare_routine(
                            name, 
                            node_type, 
                            [{"name": p["name"], "type": "INTEGER"} for p in params],
                            ret_type=node.get("return_type", "void")
                        )

        print("\n!! AFTER FIRST PASS !!") #debug
        self.symbols.dump() #debug

        # PASS 2: full analysis
        for node in nodes:
            self.visit(node)

        print("\n!! FINAL !!") #debug
        self.symbols.dump() #debug

    # ---- PROGRAM  ----

    def visit_program(self, node):
        self.symbols.push_var_scope()
        self.symbols.push_label_scope()

        for stmt in node["body"]:
            self.visit(stmt)

        self.symbols.check_undefined_labels()

        #self.symbols.pop_label_scope()
        #self.symbols.pop_var_scope()

    # ---- VISITS ----

    def visit(self, node):
        if node is None: return

        if isinstance(node, list):
            for n in node: self.visit(n)
            return

        if isinstance(node, (int, float, str, bool)):
            return self.visit_literal(node)

        node_type = node.get("type") or node.get("node")

        # skip nodes like empty dicts
        if not node_type:
            return

        method_name = f"visit_{node_type}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        self.errors.append(SemanticError(f"No visit method for node type: {node.get("type")}"))
    
    # ---- EXPRESSIONS ----

    def eval_expr(self, node):
        return self.visit(node)

    def visit_literal(self, value):
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, float):
            return "REAL"
        if isinstance(value, str):
            return "CHARACTER"

    def visit_id(self, node):
        name = node["name"]
    
        var = self.symbols.lookup_var(name)
    
        if var and not var["initialized"]:
            self.errors.append(SemanticError(f"Variable '{name}' used before initialization"))
    
        return var["type"] if var else "INTEGER"

    def visit_function(self, node):
        return self._visit_routine(node, "function")
    
    def visit_subroutine(self, node):
        return self._visit_routine(node, "subroutine")
    
    def _visit_routine(self, node, kind):
            name = node["name"]
            params = node.get("params", [])

            self.symbols.push_var_scope()
            self.symbols.push_label_scope()

            # a function's name doubles as the variable that holds its return value.
            # if the routine kind is a "function", the analyzer declares the routine's
            # name as a local variable within the new scope.
            if kind == "function":
                ret_type = node.get("return_type", "INTEGER")
                self.symbols.declare_var(name, ret_type)

            for p in params:
                self.symbols.declare_var(p["name"], "INTEGER")
                self.symbols.initialize(p["name"])

            for stmt in node["body"]:
                self.visit(stmt)

            self.symbols.check_undefined_labels()
            self.symbols.pop_label_scope()
            self.symbols.pop_var_scope()

    def visit_binop(self, node):
        left = self.visit(node["left"])
        right = self.visit(node["right"])
        op = node["op"]

        # relational ops → LOGICAL
        if op in [".GT.", ".LT.", ".EQ.", ".NE.", ".GE.", ".LE."]:
            return "LOGICAL"

        # arithmetic
        if left == "REAL" or right == "REAL":
            return "REAL"

        return "INTEGER"

    # ---- STATEMENTS ----
    
    def visit_statement(self, node):
        body = node.get("body")
        if body:
            self.visit(body)

    def visit_continue(self, node):
        pass

    def visit_assignment(self, node):           # check var type matching ?
            var_name = node["variable"]["name"]
            expr_type = self.visit(node["expression"])

            self.symbols.lookup_var(var_name)
            self.symbols.initialize(var_name)

    def visit_declaration(self, node):
        dtype = node["dtype"]

        for var in node["variables"]:
            self.symbols.declare_var(var["name"], dtype)

    def visit_call(self, node):
        name = node["name"]
        args = node.get("args", [])

        kind, _ = self.symbols.check_fun_call(
            name, args, self.visit
        )

        if kind == "function":
            pass  # ---- optional warning

    def visit_if(self, node):
        cond_type = self.visit(node["condition"])

        if cond_type != "LOGICAL":
            self.errors.append(SemanticError("IF condition must be LOGICAL"))

        for stmt in node["then"]:
            self.visit(stmt)

        for stmt in node.get("else", []):
            self.visit(stmt)

    def visit_do(self, node):
        var = node["var"]

        self.symbols.declare_var(var, "INTEGER")
        self.symbols.initialize(var)

        self.visit(node["start"])
        self.visit(node["stop"])

        if node.get("step"):
            self.visit(node["step"])

        self.symbols.define_label(node["label"])

        for stmt in node["body"]:
            self.visit(stmt)

    # ---- LABELS ----

    def visit_goto(self, node):
        label = node["label"]
        self.symbols.declare_label(label)

    def visit_label(self, node):
        label = node["label"]
        self.symbols.define_label(label)

    def visit_read(self, node):
        for item in node["items"]:
            name = item.get("name")
            if name:
                self.symbols.lookup_var(name)
                self.symbols.initialize(name)

    def visit_print(self, node):
        for item in node["items"]:
            self.visit(item)
