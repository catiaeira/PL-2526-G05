class CodeGenSymbolTable:
    
    def __init__(self):
        self.variable_dict = {}
        self.global_index: int = 0

    def insert(self, name: str, data_type: str) -> int:
        """ Returns the index for the inserted variable. """
        index = self.global_index
        self.variable_dict[name] = (index, data_type)
        self.global_index += 1
        return index

    def lookup(self, name:str):
        """ Returns a tuple of the form (index, data_type). """
        return self.variable_dict[name]
