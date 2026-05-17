      ! comment
C     this is a comment
*     this is a comment
c     this is a comment

      PROGRAM MAIN
      INTEGER A, B
      READ(*,*) A
      B = A *
     & 10
      IF (B .GT. 50) THEN
          PRINT *, 'HIGH'
      ELSE
          PRINT *, 'LOW'
      ENDIF
5     DO 20 I = 1, 5 ! comment
          CALL LOGIT(I) !comment
   20 CONTINUE! comment
      END
!     comment

      SUBROUTINE LOGIT(VAL)
      PRINT *, VAL ! comment
      END