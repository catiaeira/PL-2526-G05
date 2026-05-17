      PROGRAM MATMULT
      INTEGER MATRIX(3,3)
      INTEGER I, J, VAL
      VAL = 1
      
      DO 10 I = 1, 3
          DO 20 J = 1, 3
              MATRIX(I, J) = VAL
              VAL = VAL + 1
   20     CONTINUE
   10 CONTINUE
   
      PRINT *, MATRIX(2, 3)
      END