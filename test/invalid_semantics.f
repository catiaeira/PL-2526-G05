      PROGRAM SEMANTICERR
      INTEGER I
      LOGICAL FLAG
      FLAG = .TRUE.
      
C -- 1. Type Mismatch: Arithmetic on Logical --
      I = 10 + FLAG
      
C -- 2. Undeclared Variable --
      K = 50
      
C -- 3. Undefined Label --
      GOTO 999
      
C -- 4. Routine Kind Mismatch --
C -- (Calling a Subroutine that doesn't exist, or using a function as a call) --
      CALL MY_FUNC(I)
      END
  
      FUNCTION MY_FUNC(N)
      INTEGER MY_FUNC, N
      MY_FUNC = N * 2
      RETURN
      END