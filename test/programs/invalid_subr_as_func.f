      PROGRAM SUBASFUNC
      INTEGER X
      
C -- ERROR: LOGIT is a subroutine (void), it cannot return a value for an expression --
      X = 10 + LOGIT(5) 
      END

      SUBROUTINE LOGIT(N)
      INTEGER N
      PRINT *, N
      END