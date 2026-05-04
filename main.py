import lexer as fortran_lexer
import parser as fortran_parser

def dump_tokens(text):
    from lexer import build_lexer
    lex = build_lexer()
    lex.input(text)
    while True:
        tok = lex.token()
        if not tok:
            break
        print(f"  L{tok.lineno:3}  {tok.type:<20} {repr(tok.value)}: {tok.lexpos}")

def main():
    code = """\
      PROGRAM MAIN
      INTEGER A, B
      READ(*,*) A
      B = A * 10
      IF (B .GT. 50) THEN
          PRINT *, 'HIGH'
      ELSE
          PRINT *, 'LOW'
      ENDIF
      DO 20 I = 1, 5
          CALL LOGIT(I)
   20 CONTINUE
      END

      SUBROUTINE LOGIT(VAL)
      PRINT *, VAL
      END
"""
    test_code = '''\
        PROGRAM HELLO
        PRINT *, 'Ola, Mundo!'
        END
'''

    print("=== TOKENS ===")
    dump_tokens(code)
    print("=== PARSE ===")
    result = fortran_parser.parse(code)
    print(result)

if __name__ == '__main__':
    main()