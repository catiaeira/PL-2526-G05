import lexer as fortran_lexer
import parser as fortran_parser
from semantic import SemanticAnalyzer

def dump_tokens(text):
    from lexer import build_lexer
    lex = build_lexer()
    lex.input(text)
    while True:
        tok = lex.token()
        if not tok:
            break
        print(f"  L{tok.lineno:3}  {tok.type:<20} {repr(tok.value)}: {tok.lexpos}")

def preprocess (code): # truncates code after col 72
    lines = code.splitlines()

    truncated_lines = [line[:72] for line in lines]
    return "\n".join(truncated_lines)

def valid_programs():
    v_programs = {
        "1": "exemplo1.f",
        "2": "exemplo2.f",
        "3": "exemplo3.f",
        "4": "exemplo4.f",
        "5": "exemplo5.f",
        "6": "code.f",
        "7": "valid_features.f",
        "8": "valid_logic.f",
        "9": "valid_computed_goto.f"
    }

    print("Available test files:")
    for key, filename in v_programs.items():
        print(f"{key} - {filename}")

    option = input().strip()

    if option not in v_programs:
        print("Invalid option")
        return 0
    
    return v_programs[option]


def invalid_programs():
    i_programs = {
        "1": "invalid_syntax.f",
        "2": "invalid_semantics.f"
    }

    print("Available test files:")
    for key, filename in i_programs.items():
        print(f"{key} - {filename}")

    option = input().strip()
    
    if option not in i_programs:
        print("Invalid option")
        return 0
    
    return i_programs[option]

def main():
    print("Run:")
    print("1 - Valid Programs")
    print("2 - Invalid Programs")

    option = input().strip()
    
    match option:
        case "1":
            p = valid_programs()
        case "2":
            p = invalid_programs()
        case "0":
            print("Exiting...")
            return
        case _:
            print("Invalid option")
            return

    if p == "0":
        print("Exiting...")

    try:
        path = f"test/{p}"
        with open(path, 'r') as f:
            source = f.read()

        print("\n=== TOKENS ===")
        source = preprocess(source)
        dump_tokens(source)

        print("\n=== PARSE ===")
        ast = fortran_parser.parse(source)
        print(ast)

        print("\n=== SEMANTIC ANALYSIS ===")
        analyzer = SemanticAnalyzer()
        valid = analyzer.analyze(ast)

        if not valid:
            return

        ## else carry on to machine code generation
    except Exception as e:
        print(f"  [-] Unexpected failure: {e}")

if __name__ == '__main__':
    main()