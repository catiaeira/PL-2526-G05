      PROGRAM STRESSTEST1
      INTEGER I, J, RES
      REAL X
      I = 10
      X = 5.5
      
C -- ERROR 1: IF condition must evaluate to LOGICAL (Gets REAL from binop) --
      IF (X + 2.0) THEN
          PRINT *, 'BAD IF CONDITION'
      ENDIF

C -- ERROR 2: Library function count mismatch (MOD expects 2 args, gets 1) --
      I = MOD(I)

C -- ERROR 3: Label referenced but never defined (No 777 CONTINUE exists) --
      DO 777 J = 1, 5
          PRINT *, J
  100 CONTINUE

C -- ERROR 4: Routine kind mismatch (Calling a FUNCTION using a CALL statement) --
      CALL CALC_VAL(I)
      END

      INTEGER FUNCTION CALC_VAL(N)
      INTEGER N
      CALC_VAL = N * 2
      RETURN
      END