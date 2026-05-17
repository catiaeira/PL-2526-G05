from symbol_table import SymbolTable, SemanticError

class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()
        self.errors = []

    # ---- HELPERS ----

    # generic caller to catch exceptions raise by the symbol table
    def _try_catch(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except SemanticError as e:
            self.errors.append(e)
            return None

    def _get_binop_type(self, left, right, op):
        numeric = ["INTEGER", "REAL"]
        if left in numeric and right in numeric:
            return "REAL" if "REAL" in [left, right] else "INTEGER"
        if op == "CONCAT" and left == "CHARACTER" and right == "CHARACTER":
            return "CHARACTER"
        if op in [".EQ.", ".NE.", ".GT.", ".LT.", ".GE.", ".LE."]:
            return "LOGICAL"
        return "UNKNOWN"

    # ---- ENTRY POINT ----
    def analyze(self, ast):
            nodes = ast if isinstance(ast, list) else [ast]

            # PASS 1: register routine names and set parameters to UNKNOWN
            for node in nodes:
                node_type = node.get("node")
                if node_type in ("function", "subroutine"):
                    self._try_catch(
                        self.symbols.declare_routine,
                        node.get("name"),
                        node_type,
                        [{"name": p["name"], "type": "UNKNOWN"} for p in node.get("parameters", [])],
                        ret_type=node.get("return_type", "void")
                    )
                elif node_type == "program":
                    self._try_catch(self.symbols.declare_routine, node.get("name"), node_type)

            #print("\n!! POST 1ST PASS !!") #debug
            #self.symbols.dump() #debug

            # PASS 2: visit functions/subroutines first to update their signatures
            for node in nodes:
                if node.get("node") in ("function", "subroutine"):
                    self.visit(node)
            
            #print("\n!! POST 2ND PASS !!") #debug
            #self.symbols.dump() #debug

            # PASS 3: program analysis
            for node in nodes:
                if node.get("node") == "program":
                    self.visit(node)

            #print("\n!! FINAL !!") #debug
            #self.symbols.dump() #debug

            if self.errors:
                print("\nSemantic Errors Found:")
                for err in self.errors: print(f" - {err}")
                print()
                return 0

            print("Analysis complete: Program is semantically valid\n")
            return 1

    # ---- VISITOR ----

    def visit(self, node):
        if node is None: return
        
        if isinstance(node, list):
            for n in node: self.visit(n)
            return

        node_type = node.get("node") if isinstance(node, dict) else None
        
        if node_type == "labeled_statement":
            self._try_catch(self.symbols.define_label, node["label"])
            return self.visit(node["statement"])

        method_name = f"visit_{node_type}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        self.errors.append(SemanticError(f"No visit method for node type: {node.get('node')}"))

    # ---- LITERALS & REFERENCES ----

    def visit_integer_literal(self, node):
        return "INTEGER"
    
    def visit_real_literal(self, node):
        return "REAL"
    
    def visit_string_literal(self, node):
        return "CHARACTER"
    
    def visit_logical_literal(self, node):
        return "LOGICAL"

    def visit_variable_reference(self, node):
        var = self._try_catch(self.symbols.lookup_var, node["name"])
        if var and not var["initialized"]:
            self.errors.append(SemanticError(f"Variable '{node['name']}' used before initialization"))
        return var["type"] if var else "UNKNOWN"

    def visit_array_reference(self, node):
        var = self._try_catch(self.symbols.lookup_var, node["name"])
        if var and not var["initialized"]:
            self.errors.append(SemanticError(f"Array '{node['name']}' used before initialization"))
        for idx in node.get("indices", []):
            if self.visit(idx) != "INTEGER":
                self.errors.append(SemanticError(f"Array index for '{node['name']}' must be INTEGER"))
        return var["type"] if var else "UNKNOWN"

    # ---- EXPRESSIONS ----

    def visit_binary_operation(self, node):
        left, right = self.visit(node["left"]), self.visit(node["right"])
        op = node["operator"]
        if op == "CONCAT": return "CHARACTER"
        if op in [".GT.", ".LT.", ".EQ.", ".NE.", ".GE.", ".LE.", ".AND.", ".OR.", ".NOT.", ".EQV.", ".NEQV."]:
            return "LOGICAL"
        return self._get_binop_type(left, right, op)

    def visit_unary_operation(self, node):
        op_type = self.visit(node["operand"])
        op = node["operator"]
        if op == ".NOT.":
            if op_type != "LOGICAL": self.errors.append(SemanticError(".NOT. requires LOGICAL"))
            return "LOGICAL"
        if op in ["-", "+"]:
            if op_type not in ["INTEGER", "REAL"]: self.errors.append(SemanticError(f"{op} requires numeric"))
            return op_type
        return "UNKNOWN"

    def visit_function_call(self, node):
        # the parser can't distinguish NUMS(I) (array) from SIN(X) (function).
        # so we check the symbol table first, and, if it's a known array, handle it
        var = self.symbols.lookup_var(node["name"])
        if var and var.get("is_array"):
            if not var["initialized"]:
                self.errors.append(SemanticError(f"Array '{node['name']}' used before initialization"))
            for arg in node.get("arguments", []):
                if self.visit(arg) != "INTEGER":
                    self.errors.append(SemanticError(f"Array index for '{node['name']}' must be INTEGER"))
            return var["type"]
    
        # else, treat it as a genuine function call.
        arg_types = [self.visit(arg) for arg in node.get("arguments", [])]
        res = self._try_catch(self.symbols.check_call, node["name"], arg_types)
        if res:
            kind, ret_type = res
            if kind != "function":
                self.errors.append(SemanticError(f"Cannot call {kind} '{node['name']}' as function"))
            return ret_type
        return "UNKNOWN"

    # ---- ROUTINES & BLOCKS ----

    def visit_program(self, node):
        self.visit(node["body"])
        self._try_catch(self.symbols.check_undefined_labels)

    def visit_function(self, node):
        return self._visit_routine(node, "function")
    
    def visit_subroutine(self, node):
        return self._visit_routine(node, "subroutine")

    def _visit_routine(self, node, kind):
        name = node["name"]
        self.symbols.push_var_scope()
        self.symbols.push_label_scope()

        # define parameters in the new scope with UNKNOWN type initially
        for p in node.get("parameters", []):
            self.symbols.declare_var(p["name"], "UNKNOWN") 
            self.symbols.initialize(p["name"])

        # visit the body (updates from UNKNOWN to REAL/INTEGER if they're declared as variables in the body)
        self.visit(node["body"])

        # the rest is resolved by implicit typing
        for p in node.get("parameters", []):
            var_info = self.symbols.lookup_var(p["name"])
            if var_info and var_info["type"] == "UNKNOWN":
                var_info["type"] = self.symbols._get_implicit_type(p["name"])

        # update the GLOBAL routine signature
        actual_params = []
        for p in node.get("parameters", []):
            var_info = self.symbols.lookup_var(p["name"])
            # we extract the correct type from the local scope
            actual_params.append({
                "name": p["name"], 
                "type": var_info["type"] if var_info else "UNKNOWN"
            })

        self._try_catch(self.symbols.update_routine_signature, name, actual_params)

        self._try_catch(self.symbols.check_undefined_labels)
        self.symbols.pop_label_scope()
        self.symbols.pop_var_scope()

    # ---- STATEMENTS ----

    def visit_assignment(self, node):
        self.visit(node["value"])
        target = node["target"]
        if target["node"] in ["variable_reference", "array_reference"]:
            self._try_catch(self.symbols.initialize, target["name"])
            if target["node"] == "array_reference":
                self.visit(target.get("indices", []))

    def visit_variable_declaration(self, node):
        for var in node["variables"]:
            dims = var.get("dimensions", {})
            self._try_catch(self.symbols.declare_var, var["name"], node["data_type"], 
                             dims.get("first_dim"), dims.get("second_dim"))

    def visit_if_statement(self, node):
        if self.visit(node["condition"]) != "LOGICAL":
            self.errors.append(SemanticError("IF condition must be LOGICAL"))
        self.visit(node["then_branch"])
        self.visit(node.get("elseif_branches", []))
        self.visit(node.get("else_branch", []))

    def visit_elseif_branch(self, node):
        if self.visit(node["condition"]) != "LOGICAL":
            self.errors.append(SemanticError("ELSEIF condition must be LOGICAL"))
        self.visit(node["body"])

    def visit_do_loop(self, node):
        self._try_catch(self.symbols.initialize, node["loop_variable"])
        self.visit([node["start"], node["end"], node.get("step")])
        self._try_catch(self.symbols.declare_label, node["label"])

    def visit_call_statement(self, node):
        arg_types = [self.visit(arg) for arg in node.get("arguments", [])]
        res = self._try_catch(self.symbols.check_routine_call, node["name"], arg_types)
        if res and res[0] == "function":
            self.errors.append(SemanticError(f"'{node['name']}' is a function; use in expression"))

    def visit_goto_statement(self, node):
        self._try_catch(self.symbols.declare_label, node["label"])

    def visit_computed_goto_statement(self, node):
        for l in node["labels"]:
            self._try_catch(self.symbols.declare_label, l)
        self.visit(node["index"])

    def visit_read_statement(self, node):
        for item in node["items"]:
            if item.get("name"): self._try_catch(self.symbols.initialize, item["name"])

    def visit_print_statement(self, node):
        self.visit(node["items"])

    def visit_write_statement(self, node):
        self.visit(node["items"])

    def visit_parameter_statement(self, node):
        for param in node["parameters"]:
            self._try_catch(self.symbols.declare_var, param["name"], self.visit(param["value"]))
            self._try_catch(self.symbols.initialize, param["name"])

    def visit_continue_statement(self, node):
        pass

    def visit_return_statement(self, node):
        value = node.get("value")
        if value is not None:
            t = self.visit(value)
            if t != "INTEGER":
                self.errors.append(SemanticError("Return code must be INTEGER"))
    
    def visit_stop_statement(self, node):
        pass
    
    def visit_save_statement(self, node):
        for var in node.get("variables", []):
            if not self.symbols.lookup_var(var["name"]):
                self.errors.append(SemanticError(f"SAVE references undeclared variable '{var['name']}'"))