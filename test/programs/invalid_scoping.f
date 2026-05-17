      PROGRAM SCOPECHECK
      INTEGER GLOBALVAR
      GLOBALVAR = 100
      CALL TARGET()
      END

      SUBROUTINE TARGET()
      INTEGER LOCALVAR
      
C -- ERROR: GLOBALVAR does not exist in this local scope --
      LOCALVAR = GLOBALVAR + 1
      PRINT *, LOCALVAR
      END