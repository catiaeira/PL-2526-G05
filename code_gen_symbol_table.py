class CodeGenSymbolTable:
    
    def __init__(self):
        self.variable_dict: dict[str, int] = {}
        self.global_index: int = 0

    def insert(self, name: str) -> int:
        """ Returns the index for the inserted variable. """
        index = self.global_index
        self.variable_dict[name] = index
        self.global_index += 1
        return index

    def lookup(self, name:str) -> int:
        return self.variable_dict[name]
