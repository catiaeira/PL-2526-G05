      PROGRAM TESTFUNCMODMUL
      INTEGER A, B, C

      PRINT *, 'Introduza A: '
      READ *, A

      PRINT *, 'Introduza B: '
      READ *, B

      PRINT *, 'Introduza C: '
      READ *, C

      PRINT *, 'Resultado de MOD((A*B), C): ', FUNC(A,B,C)

      END

      INTEGER FUNCTION FUNC(A, B, C)
      INTEGER A, B, C
      FUNC = MOD((A*B), C)
      RETURN
      END
