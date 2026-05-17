import sys
import os
from contextlib import redirect_stdout

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lexer import build_lexer
import parser as fortran_parser
from semantic import SemanticAnalyzer
from test_registry import ALL_TESTS

def verify_expected_errors(expected_errors, actual_errors):
    # if we expected no errors and caught some, immediately fail and list them
    if len(expected_errors) == 0 and len(actual_errors) != 0:
        print("\n\tExtra caught errors:")
        for a in actual_errors:
            print(f"\t* '{a}'")
        return False

    # tracking maps: 0 = unmatched, 1 = matched
    expected = {item: 0 for item in expected_errors}
    actual = {item: 0 for item in actual_errors}

    # substring matching
    for e in expected:
        for a in actual:
            if e in a:
                actual[a] = 1
                expected[e] = 1
    
    has_missing = 0 in expected.values()
    has_extra = 0 in actual.values()

    if has_missing:
        print("\nMissing expected errors:")
        for e in expected:
            if expected[e] == 0: 
                print(f"\t* '{e}'")

        # debug
        print("\nErrors caught:")
        for a in actual:
                print(f"\t* '{a}'")

    if has_extra:
        print("\nExtra caught errors:")
        for a in actual:
            if actual[a] == 0: 
                print(f"\t* '{a}'")

    # passes ONLY if we missed nothing AND caught no extra garbage
    if not has_missing and not has_extra:
        print(f"  [✓] PASS: Program failed perfectly. Matched all {len(expected_errors)} expected assertions.")
        return True
        
    return False

def run_pipeline(filename, test):
    print("\n" + "-" * 80)
    print(f"[RUNNING TEST]: {filename[9:]}")
    
    try:
        with open(filename, 'r') as f:
            source = f.read()

        # redirect all core compiler debug print() dumps away from stdout
        with open(os.devnull, 'w') as f_null:
            with redirect_stdout(f_null):
                
                # 1. Syntactic Analysis
                ast = fortran_parser.parse(source)

                # 2. Semantic Analysis
                analyzer = SemanticAnalyzer()
                if ast and not fortran_parser.syntax_errors:
                    analyzer.analyze(ast)

        # ─────────────────────────────────────────────────────────────────
        # EXTRACTION & ASSERTIONS
        # ─────────────────────────────────────────────────────────────────
        
        syntax_errors = [str(err) for err in fortran_parser.syntax_errors]
        semantic_errors = [str(err) for err in analyzer.errors]

        # Syntax Failures Detected Check
        if syntax_errors:
            if test.should_pass:
                print("[-] Result: PARSING FAILED (Unexpected Syntax Errors)")
                for err in syntax_errors: print(f"    > {err}")
                return False
            return verify_expected_errors(test.syntax_errors, syntax_errors)

        # Semantic Failures Detected Check
        if semantic_errors:
            if test.should_pass:
                print("[-] Result: ANALYSIS FAILED (Unexpected Semantic Errors)")
                for err in semantic_errors: print(f"    > {err}")
                return False
            return verify_expected_errors(test.semantic_errors, semantic_errors)

        # Compilation Finished Check
        if not test.should_pass:
            print("[-] Result: FAILED (Program compiled smoothly, but was EXPECTED to fail)")
            return False

        print("[+] Result: SUCCESS (Program Compiled)")
        return True

    except Exception as e:
        print(f"[-] Result: EXCEPTION ({type(e).__name__}: {e})")
        return False

if __name__ == "__main__":
    passed_count = 0
    
    for test in ALL_TESTS:
        path = f"programs/{test.filename}"
        if run_pipeline(path, test):
            passed_count += 1
            print(f">>> VERDICT: {test.filename} PASSED")
        else:
            print(f">>> VERDICT: {test.filename} FAILED")

    print("\n" + "="*80)
    print(f"FINAL SCORE: {passed_count}/{len(ALL_TESTS)} ({passed_count/len(ALL_TESTS)*100:.2f}%)")
    print("="*80)