      PROGRAM LOGICOP
      LOGICAL P, Q, R, S
      P = .TRUE.
      Q = .FALSE.
      
C -- Evaluates boolean equivalence and logical negation --
      R = P .EQV. Q
      S = P .NEQV. Q
      
      IF (.NOT. R .AND. S) THEN
          PRINT *, 'LOGICAL OPERATORS COVRED'
      ENDIF
      END