      PROGRAM DUPLBL
      INTEGER X
      REAL X    ! ERROR: 'A' has already been explicitly declared
      X = 1
      
   10 PRINT *, 'FIRST OCCURRENCE OF LABEL 10'
   10 X = X + 1  ! ERROR: Label 10 defined twice
      
      END