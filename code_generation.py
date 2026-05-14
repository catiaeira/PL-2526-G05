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


def generate_read(stmt_dict):
    """
    Generates code for a read statement.
    Takes a dict of the form {type: 'read', controls: ???, items: list}.
    The items list contains dicts of the form {name: string}.
    """
    instructions: list[str] = []
    for item in stmt_dict["items"]:
        var_name = item["name"]
        index, data_type = symbol_table.lookup(var_name)
        match data_type:
            case "INTEGER":
                instructions += ["READ", "ATOI", f"STOREG {index}"]

    return instructions


def generate_expression(expression):
    """
    Generates code for a single expression. Enters recursion of the expression is nested.
    Takes an expression node that can be a literal or a dict of the form {type: string, op: string, left: expression, right: expression}.
    """
    if isinstance(expression, int):
        return [f"PUSHI {expression}"]
    elif isinstance(expression, dict):
        if expression.get("node") == "id":
            var_idx, _ = symbol_table.lookup(expression["name"])
            return [f"PUSHG {var_idx}"]
        elif expression.get("type") == "binop":
            instructions: list[str] = []
            instructions += generate_expression(expression["left"])
            instructions += generate_expression(expression["right"])
            match expression["op"]:
                case "+":
                    instructions += ["ADD"]
                case "-":
                    instructions += ["SUB"]
                case "/":
                    instructions += ["DIV"]
                case "*":
                    instructions += ["MUL"]
            return instructions

    return []

def generate_assignment(stmt_dict):
    """
    Generates code for an assignment statement.
    Takes a dict of the form {type: 'assignment', variable: {node: 'var', name: string}, expression: }
    """
    var_name = stmt_dict["variable"]["name"]
    expression = stmt_dict["expression"]
    index, _ = symbol_table.lookup(var_name)
    return generate_expression(expression) + [f"STOREG {index}"]


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
        case "read":
            return generate_read(stmt_dict)
        case "assignment":
            return generate_assignment(stmt_dict)
    return []


def generate_do(do_stmt, body_stmts, start_index) -> tuple[list[str], int]:
    """
    Generates code for a DO loop.
    Takes the do_header stmt: {type: 'do_header', target_label: int, var: string, start: int|var, stop: int|var,
    step: int|var}, the list of body statements to traverse until we find CONTINUE with the correct label and
    the index of the body from where to start.
    Returns the loop instructions and the index from where to continue traversing the AST.
    """
    label = do_stmt["target_label"]
    loop_var = do_stmt["var"]
    start = do_stmt["start"]
    stop = do_stmt["stop"]
    step = do_stmt["step"]

    instructions: list[str] = []

    # first, we need to determine if stop and step are variables
    # if they're not, we need to create temporary variables and later pop them (hence saving the booleans)
    stop_temp = True
    stop_idx = -1
    if isinstance(stop, dict) and stop.get("node") == "id":
        stop_temp = False
        stop_idx, _ = symbol_table.lookup(stop["name"])
    else:
        stop_idx = symbol_table.insert_temp("__tmp__stop", "INTEGER")
        instructions += generate_expression(stop) + [f"STOREG {stop_idx}"]

    step_temp = True
    step_idx = -1
    if step is None:
        step = 1
    if isinstance(step, dict) and step.get("node") == "id":
        step_temp = False
        step_idx, _ = symbol_table.lookup(step["name"])
    else:
        step_idx = symbol_table.insert_temp("__tmp__step", "INTEGER")
        instructions += generate_expression(step) + [f"STOREG {step_idx}"]

    loop_var_idx, _ = symbol_table.lookup(loop_var)

    # if the start value is passed from a variable, we must get that value
    # otherwise, it's just an expression
    if isinstance(start, dict) and start.get("node") == "id":
        start_idx, _ = symbol_table.lookup(start["name"])
        instructions += [f"PUSHG {start_idx}"]
    else:
        instructions += generate_expression(start)
    instructions += [f"STOREG {loop_var_idx}"]

    # check loop condition
    instructions += [f"{label}:", f"PUSHG {loop_var_idx}", f"PUSHG {stop_idx}", "INFEQ", f"JZ {label}end"]

    # loop body
    i = start_index
    while i < len(body_stmts):
        full_stmt_dict = body_stmts[i]
        if full_stmt_dict["label"] == label:
            # found the CONTINUE instruction, so the loop body ends here
            i += 1
            break
        instructions += generate_stmt(full_stmt_dict)
        i += 1

    # increment
    instructions += [f"PUSHG {step_idx}", f"PUSHG {loop_var_idx}", "ADD", f"STOREG {loop_var_idx}", f"JUMP {label}", f"{label}end:"]

    # recall if we had to create temporary variable to pop the correct amount
    # for the symbol_table, the pops don't even have to match the order, they just need to be in the same amount
    npop = 0
    if stop_temp:
        symbol_table.pop_temp()
        npop += 1
    if step_temp:
        symbol_table.pop_temp()
        npop += 1
    instructions += [f"POP {npop}"]

    return (instructions, i)


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
            nstmts = len(value)
            i: int = 0
            while i < nstmts:
                full_stmt_dict = value[i]
                stmt_dict = full_stmt_dict["stmt"]
                # special handling of do loops
                if stmt_dict["type"] == "do_header":
                    do_instrs, i = generate_do(stmt_dict, value, i + 1)
                    instructions += do_instrs
                else:
                    instructions += generate_code(full_stmt_dict)
                    i += 1


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
