      PROGRAM SYNTAXERR
      INTEGER X
      X = 10
C -- Missing THEN in IF statement --
      IF (X .GT. 5) 
          PRINT *, X
      ENDIF
    
C -- Malformed Expression --
      X = 5 + * 2
      END