      PROGRAM BADARGS
      INTEGER A
      REAL B
      A = 5
      B = 4.2
      
C -- ERROR 1: Type mismatch (Expected INTEGER, got REAL) --
      CALL PROCESS(B)
      
C -- ERROR 2: Count mismatch (Expected 1 argument, provided 2) --
      CALL PROCESS(A, B)
      END

      SUBROUTINE PROCESS(X)
      INTEGER X
      PRINT *, X
      END