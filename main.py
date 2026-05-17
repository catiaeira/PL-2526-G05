import lexer as fortran_lexer
import parser as fortran_parser
from semantic import SemanticAnalyzer
from test.test_registry import get_valid_programs, get_invalid_programs

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

def display_program_menu(program_list):
    menu_map = {str(i + 1): p.filename for i, p in enumerate(program_list)}
    
    print("Available test files:")
    for key, filename in menu_map.items():
        print(f"{key} - {filename}")
        
    option = input().strip()
    if option not in menu_map:
        print("Invalid option")
        return "0"
        
    return menu_map[option]

def main():
    print("Run:")
    print("1 - Valid Programs")
    print("2 - Invalid Programs")

    option = input().strip()
    
    match option:
        case "1":
            p = display_program_menu(get_valid_programs())
        case "2":
            p = display_program_menu(get_invalid_programs())
        case "0":
            print("Exiting...")
            return
        case _:
            print("Invalid option")
            return

    if p == "0":
        return

    try:
        path = f"test/programs/{p}"
        with open(path, 'r') as f:
            source = f.read()

        print("\n=== TOKENS ===")
        source = preprocess(source)
        dump_tokens(source)

        print("\n=== PARSE ===")
        ast = fortran_parser.parse(source)
        
        if not ast:
            return
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