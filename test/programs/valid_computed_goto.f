      PROGRAM COMPGOTO
      INTEGER CHOICE, VAL
      CHOICE = 2
      
C -- Jump to 10 if CHOICE=1, 20 if CHOICE=2, 30 if CHOICE=3 --
      GOTO (10, 20, 30), CHOICE
      
   10 VAL = 101
      GOTO 40
   20 VAL = 202
      GOTO 40
   30 VAL = 303
      
   40 PRINT *, 'VALUE IS: ', VAL
      END