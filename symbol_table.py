class SemanticError(Exception):
    pass

class SymbolTable:
    def __init__(self):
        self.__table = [{}]

    def push(self):
        self.__table.append({})

    def pop(self):
        self.__table.pop()

    # ---- LOOKUPS ----

    def lookup(self, id):
        for table in reversed(self.__table):
            if id in table:
                return table[id]
        raise SemanticError(f"Undeclared identifier: {id}")

    def lookup_var(self, id):
        entry = self.lookup(id)
        kind = entry[0]
        if kind != "var":
            raise SemanticError(f"Identifier is not a variable: {id}")
        _, tpe, initialized = entry
        return (tpe, initialized)

    def lookup_fun(self, id):
        entry = self.lookup(id)
        kind = entry[0]
        if kind != "fun":
            raise SemanticError(f"Identifier is not a function: {id}")
        _, ret_type, params = entry
        return (ret_type, params)
    
    def lookup_label(self, label):
        for table in reversed(self.__table):
            if label in table:
                kind = table[label][0]
                if kind != "label":
                    raise SemanticError(f"Identifier is not a label: {label}")
                return table[label]
        raise SemanticError(f"Undefined label: {label}")

    # ---- DECLARATIONS ----

    def declare_var(self, id, tpe):
        if id in self.__table[-1]:
            raise SemanticError(f"Duplicate declaration: {id}")
        self.__table[-1][id] = ("var", tpe, False)

    def declare_fun(self, id, ret_type, params):
        if id in self.__table[-1]:
            raise SemanticError(f"Duplicate declaration: {id}")
        self.__table[-1][id] = ("fun", ret_type, params)

    def declare_label(self, label):
        # labels are integers, store in current scope
        if label in self.__table[-1]:
            raise SemanticError(f"Duplicate label: {label}")
        self.__table[-1][label] = ("label", False)  # False = not yet defined

    def define_label(self, label):
        # declare and define in one step — labels don't need forward declaration
        for table in reversed(self.__table):
            if label in table:
                if table[label] == ("label", True):
                    raise SemanticError(f"Duplicate label: {label}")
                table[label] = ("label", True)
                return
        # first time seeing this label — declare and define it
        self.__table[-1][label] = ("label", True)



    # ---- INITIALIZATION ----

    def initialize(self, id):
        for table in reversed(self.__table):
            if id in table:
                kind, tpe, _ = table[id]
                if kind != "var":
                    raise SemanticError(f"Identifier is not a variable: {id}")
                table[id] = ("var", tpe, True)
                return
        raise SemanticError(f"Undeclared variable: {id}")
    
    # ---- CHECKS ----
    def check_undefined_labels(self):
        for id, entry in self.__table[-1].items():
            if entry[0] == "label" and entry[1] == False:
                raise SemanticError(f"Label referenced but never defined: {id}")