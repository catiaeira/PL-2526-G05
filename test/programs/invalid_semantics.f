      PROGRAM SEMANTICERR
      INTEGER I
      LOGICAL FLAG
      FLAG = .TRUE.
      
C -- 1. Type Mismatch: Arithmetic on Logical --
      I = 10 + FLAG
      
C -- 2. Undefined Label --
      GOTO 999
      
C -- 3. Routine Kind Mismatch
      CALL MYFUNC(I)
      END
  
      INTEGER FUNCTION MYFUNC(N)
      INTEGER MYFUNC, N
      MYFUNC = N * 2
      RETURN
      END