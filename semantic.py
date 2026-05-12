from symbol_table import SymbolTable, SemanticError

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.errors = []

    # ---- HELPERS ----

    def implicit_type(self, name):
        return "INTEGER" if name[0].upper() in "IJKLMN" else "REAL"

    # used in analyze() to pre map a function/subroutine's parameter types
    def _extract_param_types(self, body):
        type_map = {}
        for item in body:
            stmt = item.get("stmt", item)
            if stmt.get("type") == "declaration":
                dtype = stmt["dtype"]
                for var in stmt["variables"]:
                    type_map[var["name"]] = dtype
        return type_map
    
    # ---- ENTRY POINT ----

    def analyze(self, ast):
        nodes = ast if isinstance(ast, list) else [ast]

        # PASS 1: register routines
        for node in nodes:
            node_type = node.get("type") or node.get("node")
            if node_type in ("function", "subroutine"):
                name   = node.get("name")
                params = node.get("params", [])

                type_map = self._extract_param_types(node.get("body", []))

                self.symbols.declare_routine(
                    name,
                    node_type,
                    [{"name": p["name"], "type": type_map.get(p["name"], "UNKNOWN")
                        }
                        for p in params
                    ],
                    ret_type=node.get("return_type", "void")
                )
            elif node_type == "program":
                name = node.get("name")
                params = node.get("params", [])

                self.symbols.declare_routine(
                    name, 
                    node_type
                )

        # PASS 2: full analysis
        for node in nodes:
            self.visit(node)

        print("\n!! FINAL !!") #debug
        self.symbols.dump() #debug

    # ---- PROGRAM  ----

    def visit_program(self, node):

        for stmt in node["body"]:
            self.visit(stmt)

        self.symbols.check_undefined_labels()

    # ---- VISITS ----

    def visit(self, node):
        if node is None: return
        
        if isinstance(node, list):
            for n in node: self.visit(n)
            return

        if isinstance(node, (int, float, str, bool)):
            return self.visit_literal(node)

        if "stmt" in node:
            if node.get("label") is not None:
                self.symbols.define_label(node["label"])
            return self.visit(node["stmt"])

        node_type = node.get("type") or node.get("node")
        print(f"Reading: {node}")
        print(f"Node type: {node_type}")
        if not node_type:
            return

        method_name = f"visit_{node_type}"
        method = getattr(self, method_name, self.generic_visit)
        print(f"Calling: {method_name}\n")
        return method(node)

    def generic_visit(self, node):
        self.errors.append(SemanticError(f"No visit method for node type: {node.get("type")}"))
        self.errors.append("Failing node: ")
        self.errors.append(f"{node}")
    
    # ---- EXPRESSIONS ----

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

    def visit_varOrFun(self, node):
        vname = node["name"]
        args = node.get("args", [])

        try:
            self.symbols.check_lib_call(vname, args, self.visit) # already raises exception if function is undeclared
        except SemanticError:
            try:
                self.symbols.check_fun_call(vname, args, self.visit) # already raises exception if function is undeclared
            except SemanticError:
                self.symbols.lookup_var(vname)

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
                ret_type = node.get("return_type", "VOID")
                self.symbols.declare_var(name, ret_type, None, None)

            for stmt in node["body"]:
                self.visit(stmt)

            self.symbols.check_undefined_labels()
            self.symbols.pop_label_scope()
            self.symbols.pop_var_scope()

    def visit_binop(self, node):
        left = self.visit(node["left"])
        right = self.visit(node["right"])
        op = node["op"]

        # concat
        if op == "CONCAT":
            return "CONCAT"
        
        # logical
        elif op in [".GT.", ".LT.", ".EQ.", ".NE.", ".GE.", ".LE.", ".AND.", ".OR.", ".NOT.", ".EQV.", ".NEQV."]:
            return "LOGICAL"

        # arithmetic
        elif op in ["-","+","/","*","**"]:
            return "ARITHMETIC"
        
    def visit_unop(self, node):
        operand = self.visit(node["operand"])
        op = node["op"]

        # logical
        if op == ".NOT.":
            return "LOGICAL"

        # arithmetic
        elif op in ["-","+"]:
            return "ARITHMETIC"

    # ---- STATEMENTS ----
    
    def visit_statement(self, node):
        body = node.get("body")
        if body:
            self.visit(body)

    def visit_continue(self, node):
        pass

    def visit_return(self, node):
        pass

    def visit_assignment(self, node):
        var_name = node["variable"]["name"] 
        self.symbols.initialize(var_name) # already runs lookup_var and raises exception if undeclared

    def visit_declaration(self, node):
        for var in node["variables"]:
            lower = var.get("lower")
            upper = var.get("upper")
            if not lower:
                if not upper:
                    self.symbols.declare_var(var["name"], node["dtype"], None, None)
                else:
                    self.symbols.declare_var(var["name"], node["dtype"], None, upper)
            else:
                self.symbols.declare_var(var["name"], node["dtype"], lower, upper)

    def visit_call(self, node):
        name = node["name"]
        args = node.get("args", [])

        kind, _ = self.symbols.check_fun_call(
            name, args, self.visit
        )

        if kind == "function":
            self.errors.append(SemanticError(""))

    def visit_if(self, node):
        cond_type = self.visit(node["condition"])

        if cond_type != "LOGICAL":
            self.errors.append(SemanticError("IF condition must be LOGICAL"))

        for stmt in node["then"]:
            self.visit(stmt)

        n_else = node.get("else")
        if n_else:
            for stmt in node.get("else"):
                self.visit(stmt)

    def visit_do_header(self, node):
        var = node["var"]

        try:
            self.symbols.lookup_var(var)
        except SemanticError:
            self.symbols.declare_var(var, self.implicit_type(var), None, None)
    
        self.symbols.initialize(var)

        self.visit(node["start"])
        self.visit(node["stop"])

        if node.get("step"):
            self.visit(node["step"])

        self.symbols.declare_label(node["target_label"])

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
                self.symbols.initialize(name)

    def visit_print(self, node):
        for item in node["items"]:
            self.visit(item)
