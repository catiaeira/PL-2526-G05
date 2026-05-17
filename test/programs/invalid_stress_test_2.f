      PROGRAM STRESSTEST2
      INTEGER ARR(10)
      REAL RVAL
      LOGICAL FLAG
      
      ARR(1) = 5
      RVAL = 3.14
      FLAG = .TRUE.

C -- ERROR 1: Unary minus (-) applied to non-numeric type LOGICAL --
      FLAG = -FLAG

C -- ERROR 2: Array index evaluates to LOGICAL instead of INTEGER --
      ARR(FLAG) = 20

C -- ERROR 3: Argument type mismatch (Subroutine expects INTEGER, gets REAL) --
      CALL RENDER(RVAL)
      END

      SUBROUTINE RENDER(NUM)
      INTEGER NUM
C -- ERROR 4: Duplicate variable declaration inside local subroutine scope --
      REAL NUM
      
      PRINT *, NUM
      RETURN
      END