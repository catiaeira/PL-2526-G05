import sys
import parser as fortran_parser
from code_gen_symbol_table import CodeGenSymbolTable

symbol_table_stack = [CodeGenSymbolTable(0)]
stack_pointer = 0
if_counter = 0
functions = {}  # {name: {"return_type": "", "n_params": int}}

def generate_print(stmt_dict):
    """
    Generates code for a print statement.
    Takes a dict of the form {node: 'print_statement', format: str, items: list}
    """
    format = stmt_dict["format"]
    items = stmt_dict["items"]

    instructions: list[str] = []
    for item in items:
        match item["node"]:
            case "string_literal":
                instructions += [f"PUSHS \"{item['value']}\"", "WRITES"]

            case "variable_reference":
                var_name = item["name"]
                index, data_type = symbol_table_stack[stack_pointer].lookup(var_name)
                write_instruction = ""
                match data_type:
                    case "INTEGER":
                        write_instruction = "WRITEI"
                    case "REAL":
                        write_instruction = "WRITEF"

                push_instr = f"PUSHG {index}" if stack_pointer == 0 else f"PUSHL {index}"
                instructions += [push_instr, write_instruction]

            case "binary_operation":
                instructions += generate_expression(item)
                # for now, default to integer
                instructions += ["WRITEI"]

            case "function_call":
                name = item["name"]
                # first check if this is really a function
                # if not, it's an array access
                if name in functions:
                    instructions += generate_function_call(item)
                    func_info = functions.get(name)
                    if func_info:
                        match func_info["return_type"]:
                            case "INTEGER":
                                instructions += ["WRITEI"]
                            case "LOGICAL":
                                instructions += ["WRITEI"]
                            case "REAL":
                                instructions += ["WRITEF"]
                    else:
                        print("WARNING: Function with unknown / not supported type detected in generate_print")
                elif symbol_table_stack[stack_pointer].contains(name):
                    instructions += generate_array_access(item)
                else:
                    # intrinsic or unknown
                    instructions += generate_function_call(item)
                    match name:
                        case "MOD":
                            instructions += ["WRITEI"]


    return instructions + ["WRITELN"]


def generate_declaration_integer(variables):
    """
    Generates code for an integer variable declaration.
    Takes a list of dicts of the form {node: 'variable, name: string, dimensions: {node: 'dimension,
    first_dim: int, second_dim: ???}}. dimension is only present of the variable is an array.
    """
    instructions: list[str] = []
    for var_dict in variables:
        name = var_dict["name"]
        # skip variables that are function arguments and therefore were already inserted in the symbol table
        if stack_pointer != 0 and symbol_table_stack[stack_pointer].lookup(name) != None:
            continue
        if var_dict.get("dimensions") is not None:  # means this is an array
            index = symbol_table_stack[stack_pointer].insert(name, "INTEGER_ARRAY")
            size = var_dict["dimensions"]["first_dim"]
            store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
            instructions += [f"ALLOC {size}", f"{store_instr} {index}"]
        else:
            index = symbol_table_stack[stack_pointer].insert(name, "INTEGER")
            store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
            instructions += ["PUSHI 0", f"{store_instr} {index}"]
    return instructions


def generate_declaration_logical(variables):
    """
    Generates code for a logical variable declaration.
    Takes a list of dicts of the form {name: string}
    """
    instructions: list[str] = []
    for var_dict in variables:
        name = var_dict["name"]
        # skip variables that are function arguments and therefore were already inserted in the symbol table
        if stack_pointer != 0 and symbol_table_stack[stack_pointer].lookup(name) != None:
            continue
        index = symbol_table_stack[stack_pointer].insert(name, "LOGICAL")
        store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
        instructions += ["PUSHI 0", f"{store_instr} {index}"]
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
    Takes a dict of the form {node: 'read_statement', controls: ???, items: list}.
    The items list contains dicts of the form {name: string}.
    """
    instructions: list[str] = []
    for item in stmt_dict["items"]:
        name = item["name"]
        index, data_type = symbol_table_stack[stack_pointer].lookup(name)
        if item["node"] == "function_call" and symbol_table_stack[stack_pointer].contains(name):  # this is an array access
            indices = item["arguments"]
            match data_type:
                case "INTEGER_ARRAY":
                    push_instr = f"PUSHG {index}" if stack_pointer == 0 else f"PUSHL {index}"
                    # PUSHI 1 and SUB make the translation from Fortran array indexing to the VM (1 vs 0 based)
                    instructions += [push_instr] + generate_expression(indices[0]) + ["PUSHI 1", "SUB", "READ", "ATOI", "STOREN"]
        else:
            match data_type:
                case "INTEGER":
                    store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
                    instructions += ["READ", "ATOI", f"{store_instr} {index}"]

    return instructions


def generate_array_access(expr_dict):
    """
    Generates code for an array read access.
    Takes a dict of the form {node: 'function_call', name: string, arguments: list}.
    """
    name = expr_dict["name"]
    indices = expr_dict["arguments"]

    array_idx, _ = symbol_table_stack[stack_pointer].lookup(name)
    push_instr = f"PUSHG {array_idx}" if stack_pointer == 0 else f"PUSHL {array_idx}"
    # only supporting 1d arrays for now
    # PUSHI 1 and SUB make the translation from Fortran array indexing to the VM (1 vs 0 based)
    return [push_instr] + generate_expression(indices[0]) + ["PUSHI 1", "SUB", "LOADN"]


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
            var_idx, _ = symbol_table_stack[stack_pointer].lookup(expression["name"])
            push_instr = f"PUSHG {var_idx}" if stack_pointer == 0 else f"PUSHL {var_idx}"
            return [push_instr]

        case "unary_operation":
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

        case "function_call":
            name = expression["name"]
            # check if it's really a function first
            # if not, it's an array access
            if name in functions:
                return generate_function_call(expression)
            elif symbol_table_stack[stack_pointer].contains(name):
                return generate_array_access(expression)
            else:
                # intrinsic function or error
                return generate_function_call(expression)

    print("WARNING: Added no instructions in generate_expression")
    return ["// added no instructions"]

def generate_assignment(stmt_dict):
    """
    Generates code for an assignment statement.
    Takes a dict of the form {node: 'assignment', target: {node: 'variable_reference', name: string}, value: expression}.
    The target can also be an array: {node: 'array_reference', name: string, indices: list}.
    """
    target = stmt_dict["target"]
    name = target["name"]
    value = stmt_dict["value"]
    index, _ = symbol_table_stack[stack_pointer].lookup(name)

    # here the array access appears as array_reference, not as function_call
    if target["node"] == "array_reference":
        indices = target["arguments"]
        push_instr = f"PUSHG {index}" if stack_pointer == 0 else f"PUSHL {index}"
        # PUSHI 1 and SUB make the translation from Fortran array indexing to the VM (1 vs 0 based)
        return [push_instr] + generate_expression(indices[0]) + ["PUSHI 1", "SUB"] + generate_expression(value) + ["STOREN"]
    else:
        store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
        return generate_expression(value) + [f"{store_instr} {index}"]


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


def generate_return(stmt_dict):
    """
    Generates code for a function return statement.
    Takes a dict of the form {node: 'return_statement', value: ???}
    """
    num_local_vars = symbol_table_stack[stack_pointer].get_num_local_vars()
    return [f"POP {num_local_vars}", "RETURN"]


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
        case "return_statement":
            stmt_instructions = generate_return(stmt_dict)

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
        end_idx, _ = symbol_table_stack[stack_pointer].lookup(end["name"])
    else:
        end_idx = symbol_table_stack[stack_pointer].insert_temp("__tmp__end", "INTEGER")
        store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
        instructions += generate_expression(end) + [f"{store_instr} {end_idx}"]

    step_temp = True
    step_idx = -1
    if step is None:
        step = {"node": "integer_literal", "value": 1}
    if isinstance(step, dict) and step.get("node") == "variable_reference":
        step_temp = False
        step_idx, _ = symbol_table_stack[stack_pointer].lookup(step["name"])
    else:
        step_idx = symbol_table_stack[stack_pointer].insert_temp("__tmp__step", "INTEGER")
        store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
        instructions += generate_expression(step) + [f"{store_instr} {step_idx}"]

    loop_var_idx, _ = symbol_table_stack[stack_pointer].lookup(loop_var)

    # if the start value is passed from a variable, we must get that value
    # otherwise, it's just an expression
    if isinstance(start, dict) and start.get("node") == "variable_reference":
        start_idx, _ = symbol_table_stack[stack_pointer].lookup(start["name"])
        push_instr = f"PUSHG {start_idx}" if stack_pointer == 0 else f"PUSHL {start_idx}"
        instructions += [push_instr]
    else:
        instructions += generate_expression(start)
    store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
    instructions += [f"{store_instr} {loop_var_idx}"]

    push_instr = "PUSHG" if stack_pointer == 0 else "PUSHL"
    # check loop condition
    instructions += [f"{label}:", f"\t{push_instr} {loop_var_idx}", f"\t{push_instr} {end_idx}", "\tINFEQ", f"\tJZ {label}end"]

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
    push_instr = "PUSHG" if stack_pointer == 0 else "PUSHL"
    store_instr = "STOREG" if stack_pointer == 0 else "STOREL"
    instructions += [f"\t{push_instr} {step_idx}", f"\t{push_instr} {loop_var_idx}", "\tADD", f"\t{store_instr} {loop_var_idx}", f"\tJUMP {label}", f"{label}end:"]

    # recall if we had to create temporary variable to pop the correct amount
    # for the symbol_table, the pops don't even have to match the order, they just need to be in the same amount
    npop = 0
    if end_temp:
        symbol_table_stack[stack_pointer].pop_temp()
        npop += 1
    if step_temp:
        symbol_table_stack[stack_pointer].pop_temp()
        npop += 1
    instructions += [f"POP {npop}"]

    return (instructions, i)


def generate_function_call(expr_dict):
    """
    Generates code for a function call.
    First, it matches the function name to determine if it's an intrinsic function, in which case the instructions
    are directly inlined.
    Takes a dict of the form {node: 'function_call', name: string, arguments: list}
    """
    name = expr_dict["name"]
    args = expr_dict["arguments"]
    
    # intrinsic functions
    match name:
        case "MOD":
            instructions = []
            instructions += generate_expression(args[0])
            instructions += generate_expression(args[1])
            instructions += ["MOD"]
            return instructions
        
        # case "ABS": ...
        # case "MIN": ...
        # case "MAX": ...
    
    # user-defined function - full CALL

    instructions = []

    # determine what instruction to use to reserve space for the return value based on the saved function return type
    func_info = functions.get(name)
    if func_info:
        match func_info["return_type"]:
            case "INTEGER":
                instructions += ["PUSHI 0"]
            case "LOGICAL":
                instructions += ["PUSHI 0"]
            case "REAL":
                instructions += ["PUSHF 0"]

    for arg in args:
        instructions += generate_expression(arg)
    instructions += [f"PUSHA {name}", "CALL", f"POP {len(args)}"]
    return instructions


def generate_function(func_dict):
    """
    Generates code for a function.
    Takes a dict of the form {node: 'function', name: string, return_type: string,
    parameters: list[{node: 'parameter', name: string}], body: list[stmts]}
    """
    global stack_pointer
    func_name = func_dict["name"]
    return_type = func_dict["return_type"]
    params = func_dict["parameters"]
    n_params = len(params)
    body = func_dict["body"]

    symbol_table_stack.append(CodeGenSymbolTable(-(n_params+1)))
    stack_pointer += 1

    # register function name as return variable at the bottom of the stack
    symbol_table_stack[stack_pointer].insert(func_name, return_type)

    # collect the names of the parameters
    param_to_type = {}
    for param in params:
        param_to_type[param["name"]] = "undefined"

    # traverse the body while there are variable declarations to find the type of every parameter
    for stmt_dict in body:
        if stmt_dict["node"] != "variable_declaration":
            break
        data_type = stmt_dict["data_type"]
        for var in stmt_dict["variables"]:
            if var["name"] in param_to_type:
                param_to_type[var["name"]] = data_type

    for param in params:
        name = param["name"]
        data_type = param_to_type.get(name)
        # implicit types
        if data_type is None:
            data_type = "INTEGER" if name[0] in "IJKLMN" else "REAL"
        symbol_table_stack[stack_pointer].insert(name, data_type)

    instructions = ["", f"{func_name}:"]
    instructions += generate_code(body)

    symbol_table_stack.pop()
    stack_pointer -= 1

    return instructions


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

    if isinstance(value, list):
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
        node = value.get("node")
        match node:
            case "program":
                print(f"Generating code for program {value['name']}")
                instructions += generate_code(value["body"])
            # this won't really happen
            case "function":
                print(f"Generating code for function {value['name']}")
                instructions += generate_function(value)

    else:
        print("WARNING: Unexpected type found when traversing the AST in generate_code")

    return instructions


def generate_code_main(ast):
    # before going to the main program, check every function header to collect the return types
    for node in ast:
        if node["node"] == "function":
            func_name = node["name"]
            return_type = node["return_type"]
            n_params = len(node["parameters"])
            functions[func_name] = {"return_type": return_type, "n_params": n_params}
    
    instructions = generate_code(ast[0])
    instructions += ["JUMP endprogram"]
    rest = ast[1:]
    for node in rest:
        match node["node"]:
            case "function":
                instructions += generate_function(node)
            case "subroutine":
                pass
    instructions += ["", "endprogram:"]
    print("\n===== VM Instructions =====\n")
    for instruction in instructions:
        print(instruction)


with open(sys.argv[1], "r") as source:
    text = source.read()
    ast = fortran_parser.parse(text)
    generate_code_main(ast)
