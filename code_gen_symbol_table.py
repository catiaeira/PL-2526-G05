class CodeGenSymbolTable:
    
    def __init__(self, index_start: int):
        self.variable_dict: dict[str, tuple[int, str]] = {}
        self.global_index: int = index_start
        self.temp_vars_stack: list[tuple[str, int, str]] = []

    def insert(self, name: str, data_type: str) -> int:
        """ Returns the index for the inserted variable. """
        index = self.global_index
        self.variable_dict[name] = (index, data_type)
        self.global_index += 1
        return index

    def insert_temp(self, name: str, data_type: str) -> int:
        """ Inserts a variable in the temporary stack, returning the index for the new variable. """
        index = self.global_index
        self.temp_vars_stack.append((name, index, data_type))
        self.global_index += 1
        return index

    def lookup(self, name: str) -> tuple[int, str] | None:
        """ Returns a tuple of the form (index, data_type). """
        return self.variable_dict.get(name)

    def pop_temp(self):
        """ Removes the most recent temporary variable and decrements the global index by 1. """
        self.temp_vars_stack.pop()
        self.global_index -= 1

    def contains(self, name: str) -> bool:
        """ Checks if a variable name is part of the symbol table. """
        return name in self.variable_dict
