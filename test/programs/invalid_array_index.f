      PROGRAM BADINDEX
      INTEGER ARR(5)
      REAL X
      ARR(1) = 10
      X = 2.5
      
C -- ERROR: Array index evaluates to REAL instead of INTEGER --
      PRINT *, ARR(X)
      END