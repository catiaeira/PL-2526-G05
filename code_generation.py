import sys
import parser as fortran_parser
from code_gen_symbol_table import CodeGenSymbolTable

symbol_table = CodeGenSymbolTable()

def generate_print(stmt_dict):
    """
    Generates code for a print statement.
    Takes a dict of the form {type: 'print', format: str, items: list}
    """
    format = stmt_dict["format"]
    items = stmt_dict["items"]

    print(f"format={format}")
    instructions: list[str] = []
    for item in items:
        if isinstance(item, str):
            instructions += [f"PUSHS \"{item}\"", "WRITES"]
        elif isinstance(item, dict):
            var_name = item["name"]
            index, data_type = symbol_table.lookup(var_name)
            write_instruction = ""
            match data_type:
                case "INTEGER":
                    write_instruction = "WRITEI"
            instructions += [f"PUSHG {index}", write_instruction]

    return instructions + ["WRITELN"]


def generate_declaration_integer(variables):
    """
    Generates code for an integer variable declaration.
    Takes a list of dicts of the form {name: string}
    """
    instructions: list[str] = []
    for var_dict in variables:
        index = symbol_table.insert(var_dict["name"], "INTEGER")
        instructions += ["PUSHI 0", f"STOREG {index}"]
    return instructions


def generate_declaration(stmt_dict):
    """
    Generates code for a variable declaration statement.
    Takes a dict of the form {type: 'declaration', dtype: string, variables: list}.
    """
    data_type = stmt_dict["dtype"]
    match data_type:
        case "INTEGER":
            return generate_declaration_integer(stmt_dict["variables"])
    return []


def generate_stmt(full_stmt_dict):
    """
    Generates code for a single statement.
    Takes a dict of the form {label: int, stmt: dict}
    """
    print(f"label={full_stmt_dict['label']}")
    stmt_dict = full_stmt_dict["stmt"]
    stmt_type = stmt_dict["type"]
    match stmt_type:
        case "print":
            return generate_print(stmt_dict)
        case "declaration":
            return generate_declaration(stmt_dict)
    return []


def generate_code(value):
    """
    Generates the machine instructions by traversing the AST recursively.
    """

    instructions = []

    if value is None:
        pass

    elif isinstance(value, bool):
        pass

    elif isinstance(value, (int, float)):
        pass

    elif isinstance(value, str):
        pass

    elif isinstance(value, list):
        if value[0].get("stmt") is not None:
            for stmt_dict in value:
                instructions += generate_code(stmt_dict)

    elif isinstance(value, dict):
        if value.get("type") == "program":
            print(f"Generating code for program {value['name']}")
            instructions += generate_code(value["body"])
        elif value.get("stmt") is not None:
            instructions += generate_stmt(value)

    else:
        pass

    return instructions


with open(sys.argv[1], "r") as source:
    text = source.read()
    ast = fortran_parser.parse(text)

instructions = generate_code(ast[0])
print("\n===== VM Instructions =====\n")
for instruction in instructions:
    print(instruction)
