import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lexer import build_lexer
from parser import parser
from semantic import SemanticAnalyzer

def run_pipeline(filename, expect_success=True):
    print(f"\n[RUNNING TEST]: {filename}")
    print("-" * 30)
    
    try:
        with open(filename, 'r') as f:
            source = f.read()

        # 1. Parsing
        ast = parser.parse(source, lexer=build_lexer())
        if ast is None:
            print("[-] Result: FAILED (Syntax Error)")
            return not expect_success

        # 2. Semantic Analysis
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        # Check for errors caught by _try_catch in your SemanticAnalyzer
        if analyzer.errors:
            print(f"[-] Result: FAILED (Semantic Errors Detected)")
            for err in analyzer.errors:
                print(f"    > {err}")
            return not expect_success

        # 3. Machine Code Generation (Mockup)
        # In a real scenario, you'd call your code generator here:
        # code = generator.generate(ast)
        print("[+] Result: SUCCESS (Program Compiled)")
        return expect_success

    except Exception as e:
        print(f"[-] Result: EXCEPTION ({type(e).__name__}: {e})")
        return not expect_success

if __name__ == "__main__":
    tests = [
        ("exemplo1.f", True),
        ("exemplo2.f", True),
        ("exemplo3.f", True),
        ("exemplo4.f", True),
        ("exemplo5.f", True),
        ("code.f", True),
        ("valid_features.f", True),
        ("valid_logic.f", True),
        ("valid_computed_goto.f", True)
        ("invalid_syntax.f", False),
        ("invalid_semantics.f", False)
    ]

    passed_count = 0
    for file, expected in tests:
        if run_pipeline(file, expected):
            passed_count += 1
            print(">>> VERDICT: TEST PASSED")
        else:
            print(">>> VERDICT: TEST FAILED")

    print("\n" + "="*30)
    print(f"FINAL SCORE: {passed_count}/{len(tests)}")
    print("="*30)