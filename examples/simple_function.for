      PROGRAM SIMPLEFUNCTION
      INTEGER N, M
      N = 3
      M = 4
      PRINT *, 'Result: ', MUL(N, M)
      END

      INTEGER FUNCTION MUL(A, I)
      INTEGER A
      MUL = A * I
      RETURN
      END
