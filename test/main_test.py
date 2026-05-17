import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lexer import build_lexer
import parser as fortran_parser
from semantic import SemanticAnalyzer
from test_registry import ALL_TESTS

def run_pipeline(filename, expect_success=True):
    print("\n" + "-" * 80)
    print(f"[RUNNING TEST]: {filename}")
    
    try:
        with open(filename, 'r') as f:
            source = f.read()

        ast = fortran_parser.parse(source)

        if fortran_parser.syntax_errors:
            print(f"[-] Result: FAILED (Syntax Errors)")
            return not expect_success

        if not ast:
            print("[-] Result: FAILED (Empty AST)")
            return not expect_success

        # 2. Semantic Analysis
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        if analyzer.errors:
            print(f"[-] Result: FAILED (Semantic Errors)")
            return not expect_success

        # 3. Machine Code Generation (Mockup)
        print("[+] Result: SUCCESS (Program Compiled)")
        return expect_success

    except Exception as e:
        print(f"[-] Result: EXCEPTION ({type(e).__name__}: {e})")
        return not expect_success

if __name__ == "__main__":
    passed_count = 0
    
    for test in ALL_TESTS:
        path = f"programs/{test.filename}"
        if run_pipeline(path, test.should_pass):
            passed_count += 1
            print(f">>> VERDICT: {test.filename} PASSED")
        else:
            print(f">>> VERDICT: {test.filename} FAILED")

    print("\n" + "="*80)
    print(f"FINAL SCORE: {passed_count}/{len(ALL_TESTS)}")
    print("="*80)