import lexer as fortran_lexer
import parser as fortran_parser
from semantic import SemanticAnalyzer, SemanticError, SymbolTable

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
    print("Options:")
    print("code | e1 | e2 | e3 | e4 | e5")
    option = input().strip()

    code = """\
      ! comment
C     this is a comment
*     this is a comment
c     this is a comment

      PROGRAM MAIN
      INTEGER A, B
      READ(*,*) A
      B = A *
     2 10
      IF (B .GT. 50) THEN
          PRINT *, 'HIGH'
      ELSE
          PRINT *, 'LOW'
      ENDIF
5     DO 20 I = 1, 5 ! comment
          CALL LOGIT(I) !comment
   20 CONTINUE! comment
      END

      SUBROUTINE LOGIT(VAL)
      PRINT *, VAL ! comment
      END
"""

    e1 = '''\
      PROGRAM HELLO
      PRINT *, 'Ola, Mundo!'
      END
'''

    e2 = '''\
      PROGRAM FATORIAL
      INTEGER N, I, FAT
      PRINT *, 'Introduza um numero inteiro positivo:'
      READ *, N
      FAT = 1
      DO 10 I = 1, N
      FAT = FAT * I
   10 CONTINUE
      PRINT *, 'Fatorial de ', N, ': ', FAT
      END
'''

    e3 = '''\
      PROGRAM PRIMO
      INTEGER NUM, I
      LOGICAL ISPRIM
      PRINT *, 'Introduza um numero inteiro positivo:'
      READ *, NUM
      ISPRIM = .TRUE.
      I = 2
   20 IF (I .LE. (NUM/2) .AND. ISPRIM) THEN
          IF (MOD(NUM, I) .EQ. 0) THEN
             ISPRIM = .FALSE.
          ENDIF
          I = I + 1
          GOTO 20
      ENDIF
      IF (ISPRIM) THEN
          PRINT *, NUM, ' e um numero primo'
      ELSE
          PRINT *, NUM, ' nao e um numero primo'
      ENDIF
      END
'''

    e4 = '''\
      PROGRAM SOMAARR
      INTEGER NUMS(5)
      INTEGER I, SOMA
      SOMA = 0
      PRINT *, 'Introduza 5 numeros inteiros:'
      DO 30 I = 1, 5
          READ *, NUMS(I)
          SOMA = SOMA + NUMS(I)
   30 CONTINUE
      PRINT *, 'A soma dos numeros e: ', SOMA
      END
'''

    e5 = '''\
      PROGRAM CONVERSOR
      INTEGER NUM, BASE, RESULT, CONVRT
      PRINT *, 'INTRODUZA UM NUMERO DECIMAL INTEIRO:'
      READ *, NUM
      DO 10 BASE = 2, 9
          RESULT = CONVRT(NUM, BASE)
          PRINT *, 'BASE ', BASE, ': ', RESULT
   10 CONTINUE
      END
      INTEGER FUNCTION CONVRT(N, B)
      INTEGER N, B, QUOT, REM, POT, VAL
      VAL = 0
      POT = 1
      QUOT = N
   20 IF (QUOT .GT. 0) THEN
          REM = MOD(QUOT, B)
          VAL = VAL + (REM * POT)
          QUOT = QUOT / B
          POT = POT * 10
          GOTO 20
      ENDIF
      CONVRT = VAL
      RETURN
      END
'''

    programs = {
        "code": code,
        "e1": e1,
        "e2": e2,
        "e3": e3,
        "e4": e4,
        "e5": e5,
    }

    if option not in programs:
        print("Invalid option")
        return

    source = programs[option]

    print("\n=== TOKENS ===")
    dump_tokens(source)
    
    print("\n=== PARSE ===")
    ast = fortran_parser.parse(source)
    print(ast)
    
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    if not analyzer.errors + analyzer.symbols.errors:
        print("Program is semantically correct")
    else: print("\nErrors: ", analyzer.errors + analyzer.symbols.errors, "\n")


if __name__ == '__main__':
    main()