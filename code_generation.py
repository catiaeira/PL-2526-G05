import sys
import parser as fortran_parser
from code_gen_symbol_table import CodeGenSymbolTable

symbol_table = CodeGenSymbolTable()
if_counter = 0

def generate_print(stmt_dict):
    """
    Generates code for a print statement.
    Takes a dict of the form {node: 'print_statement', format: str, items: list}
    """
    format = stmt_dict["format"]
    items = stmt_dict["items"]

    instructions: list[str] = []
    for item in items:
        node = item["node"]
        if node == "string_literal":
            instructions += [f"PUSHS \"{item['value']}\"", "WRITES"]
        elif node == "variable_reference":
            var_name = item["name"]
            index, data_type = symbol_table.lookup(var_name)
            write_instruction = ""
            match data_type:
                case "INTEGER":
                    write_instruction = "WRITEI"
                case "REAL":
                    write_instruction = "WRITEF"

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


def generate_declaration_logical(variables):
    """
    Generates code for a logical variable declaration.
    Takes a list of dicts of the form {name: string}
    """
    instructions: list[str] = []
    for var_dict in variables:
        index = symbol_table.insert(var_dict["name"], "LOGICAL")
        instructions += ["PUSHI 0", f"STOREG {index}"]
    return instructions


def generate_declaration(stmt_dict):
    """
    Generates code for a variable declaration statement.
    Takes a dict of the form {type: 'declaration', dtype: string, variables: list}.
    """
    data_type = stmt_dict["data_type"]
    match data_type:
        case "INTEGER":
            return generate_declaration_integer(stmt_dict["variables"])
        case "LOGICAL":
            return generate_declaration_logical(stmt_dict["variables"])

    print("WARNING: Added no instructions in generate_declaration")
    return ["// added no instructions"]


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
    Generates code for a single expression. Enters recursion if the expression is nested.
    Takes an expression node that can be a simple dict {node: "<something>_literal", value: literal}
    or a dict with operations (e.g., binary_operation)
    """
    if not isinstance(expression, dict):  # this should never happen
        print("WARNING: Added no instructions in generate_expression")
        return ["// added no instructions"]

    node = expression["node"]

    match node:
        case "integer_literal":
            return [f"PUSHI {expression['value']}"]

        case "logical_literal":
            return [f"PUSHI {1 if expression['value'] else 0}"]

        case "real_literal":
            return [f"PUSHF {expression['value']}"]

        case "string_literal":
            return [f"PUSHS \"{expression['value']}\""]

        case "variable_reference":
            var_idx, _ = symbol_table.lookup(expression["name"])
            return [f"PUSHG {var_idx}"]

        case "unary_opeation":
            instructions = []
            instructions += generate_expression(expression["operand"])
            match expression["operator"]:
                case ".NOT.":
                    instructions += ["NOT"]

            return instructions

        case "binary_operation":
            instructions = []
            instructions += generate_expression(expression["left"])
            instructions += generate_expression(expression["right"])
            # TODO: add support for REAL binary operations (FADD, FSUB, ...)
            match expression["operator"]:
                case "+":
                    instructions += ["ADD"]
                case "-":
                    instructions += ["SUB"]
                case "/":
                    instructions += ["DIV"]
                case "*":
                    instructions += ["MUL"]
                case ".AND.":
                    instructions += ["AND"]
                case ".OR.":
                    instructions += ["OR"]
                case ".EQ.":
                    instructions += ["EQUAL"]
                case ".NE.":
                    instructions += ["EQUAL", "NOT"]
                case ".LT.":
                    instructions += ["INF"]
                case ".LE.":
                    instructions += ["INFEQ"]
                case ".GT.":
                    instructions += ["SUP"]
                case ".GE.":
                    instructions += ["SUPEQ"]
            return instructions

    print("WARNING: Added no instructions in generate_expression")
    return ["// added no instructions"]

def generate_assignment(stmt_dict):
    """
    Generates code for an assignment statement.
    Takes a dict of the form {node: 'assignment', target: {node: 'variable_reference', name: string}, value: expression}.
    """
    var_name = stmt_dict["target"]["name"]
    expression = stmt_dict["value"]
    index, _ = symbol_table.lookup(var_name)
    return generate_expression(expression) + [f"STOREG {index}"]


def generate_goto(stmt_dict):
    """
    Generates code for a GOTO statement.
    Takes a dict of the form {node: 'goto_statement', label: int}.
    """
    label = stmt_dict["label"]
    return [f"JUMP {label}"]


def generate_if(stmt_dict):
    """
    Generates code for an IF statement.
    Takes a dict of the form {node: 'if_statement', condition: , then_branch: list[stmts], elsif_branches: list,
    else_branch: list[stmts]}
    """
    global if_counter
    n = if_counter
    if_counter += 1

    condition = stmt_dict["condition"]
    then_branch = stmt_dict["then_branch"]
    elseif_branches = stmt_dict["elseif_branches"]
    else_branch = stmt_dict["else_branch"]

    has_elseif = len(elseif_branches) > 0
    has_else = else_branch is not None and len(else_branch) > 0

    instructions: list[str] = []

    instructions += generate_expression(condition)
    if has_elseif:
        instructions += [f"JZ elseif{n}_0"]
    elif has_else:
        instructions += [f"JZ else{n}"]
    else:
        instructions += [f"JZ endif{n}"]

    instructions += generate_code(then_branch)
    instructions += [f"JUMP endif{n}"]

    for idx, branch in enumerate(elseif_branches):
        next_label = f"elseif{n}_{idx+1}" if idx+1 < len(elseif_branches) else (f"else{n}" if has_else else f"endif{n}")
        instructions += [f"elseif{n}_{idx}:"]
        instructions += generate_expression(branch["condition"])
        instructions += [f"JZ {next_label}"]
        instructions += generate_code(branch["body"])
        instructions += [f"JUMP endif{n}"]

    if has_else:
        instructions += [f"else{n}:"]
        instructions += generate_code(else_branch)

    instructions += [f"endif{n}:"]
    return instructions


def generate_stmt(label, stmt_dict):
    """
    Generates code for a single statement.
    Takes a label (can be None) and a dict of the form {node: string, ...} (the rest of the keys depend on the node type)
    """
    node = stmt_dict["node"]
    label_instruction: list[str] = [f"{label}:"] if label else []
    stmt_instructions: list[str] = []
    match node:
        case "print_statement":
            stmt_instructions = generate_print(stmt_dict)
        case "variable_declaration":
            stmt_instructions = generate_declaration(stmt_dict)
        case "read_statement":
            stmt_instructions = generate_read(stmt_dict)
        case "assignment":
            stmt_instructions = generate_assignment(stmt_dict)
        case "goto_statement":
            stmt_instructions = generate_goto(stmt_dict)
        case "if_statement":
            stmt_instructions = generate_if(stmt_dict)

    return label_instruction + stmt_instructions


def generate_do(do_stmt, body_stmts, start_index) -> tuple[list[str], int]:
    """
    Generates code for a DO loop.
    Takes the do_header stmt: {type: 'do_header', target_label: int, var: string, start: int|var, end: int|var,
    step: int|var}, the list of body statements to traverse until we find CONTINUE with the correct label and
    the index of the body from where to start.
    Returns the loop instructions and the index from where to continue traversing the AST.
    """
    label = do_stmt["label"]
    loop_var = do_stmt["loop_variable"]
    start = do_stmt["start"]
    end = do_stmt["end"]
    step = do_stmt["step"]

    instructions: list[str] = []

    # first, we need to determine if end and step are variables
    # if they're not, we need to create temporary variables and later pop them (hence saving the booleans)
    end_temp = True
    end_idx = -1
    if isinstance(end, dict) and end.get("node") == "variable_reference":
        end_temp = False
        end_idx, _ = symbol_table.lookup(end["name"])
    else:
        end_idx = symbol_table.insert_temp("__tmp__end", "INTEGER")
        instructions += generate_expression(end) + [f"STOREG {end_idx}"]

    step_temp = True
    step_idx = -1
    if step is None:
        step = {"node": "integer_literal", "value": 1}
    if isinstance(step, dict) and step.get("node") == "variable_reference":
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
    instructions += [f"{label}:", f"\tPUSHG {loop_var_idx}", f"\tPUSHG {end_idx}", "\tINFEQ", f"\tJZ {label}end"]

    # loop body
    body_instructions: list[str] = []
    i = start_index
    while i < len(body_stmts):
        lbl, stmt_dict = unwrap(body_stmts[i])
        if lbl == label:
            # found the CONTINUE instruction, so the loop body ends here
            i += 1
            break
        _, inner_stmt = unwrap(body_stmts[i])
        body_instructions += generate_stmt(None, inner_stmt)
        i += 1

    # add tabs to the body instructions and concatenate them to the global instructions
    for instr in body_instructions:
        with_tab = ["\t" + instr]
        instructions += with_tab

    # increment
    instructions += [f"\tPUSHG {step_idx}", f"\tPUSHG {loop_var_idx}", "\tADD", f"\tSTOREG {loop_var_idx}", f"\tJUMP {label}", f"{label}end:"]

    # recall if we had to create temporary variable to pop the correct amount
    # for the symbol_table, the pops don't even have to match the order, they just need to be in the same amount
    npop = 0
    if end_temp:
        symbol_table.pop_temp()
        npop += 1
    if step_temp:
        symbol_table.pop_temp()
        npop += 1
    instructions += [f"POP {npop}"]

    return (instructions, i)


def unwrap(item):
    """
    Helper that given any body item, returns (label, stmt_dict)
    """
    if item.get("node") == "labeled_statement":
        return item["label"], item["statement"]
    else:
        return None, item

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
        i: int = 0
        while i < len(value):
            label, stmt_dict = unwrap(value[i])
            # special handling of do loops
            if stmt_dict.get("node") == "do_loop":
                do_instrs, i = generate_do(stmt_dict, value, i + 1)
                instructions += do_instrs
            else:
                instructions += generate_stmt(label, stmt_dict)
                i += 1

    elif isinstance(value, dict):
        if value.get("node") == "program":
            print(f"Generating code for program {value['name']}")
            instructions += generate_code(value["body"])

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
