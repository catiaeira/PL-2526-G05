import sys
import parser as fortran_parser


def generate_print(stmt_dict):
    """
    Generates code for a print statement.
    Takes a dict of the form {type: 'print', format: str, items: list}
    """
    format = stmt_dict["format"]
    items = stmt_dict["items"]

    print(f"format={format}")
    final_string = ""
    for item in items:
        final_string += item
    return [f"PUSHS \"{final_string}\"", "WRITES"]

def generate_stmt(full_stmt_dict):
    """
    Generates code for a single statement.
    Takes a dict of the form {label: int, stmt: dict}
    """
    print(f"label={full_stmt_dict['label']}")
    stmt_dict = full_stmt_dict["stmt"]
    if stmt_dict["type"] == "print":
        return generate_print(stmt_dict)


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
        print(value)

    elif isinstance(value, dict):
        if value.get("type") == "program":
            print(f"Generating code for program {value['name']}")
            instructions += generate_code(value["body"][0])
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
