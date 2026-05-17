      PROGRAM FEATURES
      INTEGER I, J, K
      REAL X, Y, Z
      CHARACTER STR1, STR2, STR3
      LOGICAL FLAG1, FLAG2
      PARAMETER (PI = 3.14159, OFFSET = 10)
    
C -- Arithmetic and Type Promotion --
      I = 5 + OFFSET
      X = 2.5 * PI
      Y = I + X
    
C -- String Operations --
      STR1 = 'HELLO'
      STR2 = 'WORLD'
      STR3 = STR1 // STR2
    
C -- Logical and Comparison --
      FLAG1 = .TRUE.
      FLAG2 = (I .GT. 10) .AND. .NOT. (X .LT. 1.0)
    
C -- I/O Statements --
      PRINT *, STR3, FLAG2
      READ *, J
      WRITE (*, *) 'DONE', J
      END