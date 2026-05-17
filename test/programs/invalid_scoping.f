      PROGRAM SCOPECHECK
      INTEGER GLOBAL_VAR
      GLOBAL_VAR = 100
      CALL TARGET()
      END

      SUBROUTINE TARGET()
      INTEGER LOCAL_VAR
      
C -- ERROR: GLOBAL_VAR does not exist in this local scope --
      LOCAL_VAR = GLOBAL_VAR + 1
      PRINT *, LOCAL_VAR
      END