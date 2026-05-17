      PROGRAM BADUNARY
      INTEGER N
      LOGICAL FLAG
      N = 10
      FLAG = .TRUE.
      
C -- ERROR 1: .NOT. operator requires a LOGICAL operand --
      IF (.NOT. N) THEN
          PRINT *, N
      ENDIF
      
C -- ERROR 2: Unary minus (-) requires numeric type operand --
      FLAG = -FLAG
      END