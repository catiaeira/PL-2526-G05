      PROGRAM LOGIC
      INTEGER A, B, RES
      A = 20
      B = 3
    
      IF (A .GT. B) THEN
          RES = DIVIDE(A, B)
      ELSEIF (A .EQ. B) THEN
          RES = 1
      ELSE
          RES = 0
      ENDIF

      DO 100 I = 1, 5
          IF (I .EQ. 3) GOTO 50
          PRINT *, I
   50 CONTINUE
  100 CONTINUE

      PRINT *, 'FINAL RESULT: ', RES
      END

      INTEGER FUNCTION DIVIDE(X, Y)
      INTEGER X, Y
      DIVIDE = MOD(X, Y)
      RETURN
      END